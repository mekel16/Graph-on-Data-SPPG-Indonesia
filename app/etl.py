import csv
import sys
from pathlib import Path

from app.db import driver
from app.normalize import (
    clean_text,
    normalize_city,
    normalize_district,
    normalize_province,
    normalize_text,
    normalize_village,
)


def create_constraints():
    queries = [
        """
        CREATE CONSTRAINT sppg_id_unique IF NOT EXISTS
        FOR (s:SPPG)
        REQUIRE s.id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT provinsi_key_unique IF NOT EXISTS
        FOR (p:Provinsi)
        REQUIRE p.key IS UNIQUE
        """,
        """
        CREATE CONSTRAINT kabupaten_key_unique IF NOT EXISTS
        FOR (k:KabupatenKota)
        REQUIRE k.key IS UNIQUE
        """,
        """
        CREATE CONSTRAINT kecamatan_key_unique IF NOT EXISTS
        FOR (k:Kecamatan)
        REQUIRE k.key IS UNIQUE
        """,
        """
        CREATE CONSTRAINT desa_key_unique IF NOT EXISTS
        FOR (d:Desa)
        REQUIRE d.key IS UNIQUE
        """,
        """
        CREATE CONSTRAINT alamat_key_unique IF NOT EXISTS
        FOR (A:Alamat)
        REQUIRE A.key IS UNIQUE
        """,
    ]

    with driver.session() as session:
        for query in queries:
            session.run(query)

    print("Constraint selesai dibuat.")


def transform_row(row: dict, fallback_id: int) -> dict:
    """
    Menyesuaikan nama kolom dengan CSV.
    CSV memiliki kolom kosong pertama, No, provinsi, kabupaten,
    kecamatan, desa, alamat, nama SPPG.
    """

    # Menggunakan .get(..., "") agar aman terhadap nilai None sebelum clean_text
    raw_id = (
        clean_text(row.get("No", ""))
        or clean_text(row.get("", ""))
        or str(fallback_id)
    )

    # Hilangkan angka desimal seperti 1.0
    if raw_id.endswith(".0"):
        raw_id = raw_id[:-2]

    provinsi = clean_text(row.get("Provinsi SPPG", ""))
    kabupaten = clean_text(row.get("Kab./Kota SPPG", ""))
    kecamatan = clean_text(row.get("Kecamatan SPPG", ""))
    desa = clean_text(row.get("Kelurahan/Desa SPPG", ""))
    alamat = clean_text(row.get("Alamat SPPG", ""))
    nama_sppg = clean_text(row.get("Nama SPPG", ""))

    provinsi_normalized = normalize_province(provinsi)
    kabupaten_normalized = normalize_city(kabupaten)
    kecamatan_normalized = normalize_district(kecamatan)
    desa_normalized = normalize_village(desa)
    alamat_normalized = normalize_text(alamat)
    nama_normalized = normalize_text(nama_sppg)

    return {
        "id": raw_id,

        "provinsi": provinsi,
        "provinsi_normalized": provinsi_normalized,

        "kabupaten": kabupaten,
        "kabupaten_normalized": kabupaten_normalized,

        "kecamatan": kecamatan,
        "kecamatan_normalized": kecamatan_normalized,

        "desa": desa,
        "desa_normalized": desa_normalized,

        "alamat": alamat,
        "alamat_normalized": alamat_normalized,

        "nama_sppg": nama_sppg,
        "nama_normalized": nama_normalized,

        "provinsi_key": provinsi_normalized,
        "kabupaten_key": f"{provinsi_normalized}|{kabupaten_normalized}",
        "kecamatan_key": (
            f"{provinsi_normalized}|"
            f"{kabupaten_normalized}|"
            f"{kecamatan_normalized}"
        ),
        "desa_key": (
            f"{provinsi_normalized}|"
            f"{kabupaten_normalized}|"
            f"{kecamatan_normalized}|"
            f"{desa_normalized}"
        ),
        # PERBAIKAN: Alamat key dibuat hierarkis agar "Jl. Sudirman" di kota A
        # tidak menimpa / bergabung dengan "Jl. Sudirman" di kota B.
        "alamat_key": (
            f"{provinsi_normalized}|"
            f"{kabupaten_normalized}|"
            f"{kecamatan_normalized}|"
            f"{desa_normalized}|"
            f"{alamat_normalized}"
        ),
    }


def import_batch(rows: list[dict]):
    query = """
    UNWIND $rows AS row

    MERGE (p:Provinsi {key: row.provinsi_key})
    ON CREATE SET
        p.nama = row.provinsi,
        p.nama_normalized = row.provinsi_normalized

    MERGE (kk:KabupatenKota {key: row.kabupaten_key})
    ON CREATE SET
        kk.nama = row.kabupaten,
        kk.nama_normalized = row.kabupaten_normalized

    MERGE (k:Kecamatan {key: row.kecamatan_key})
    ON CREATE SET
        k.nama = row.kecamatan,
        k.nama_normalized = row.kecamatan_normalized

    MERGE (d:Desa {key: row.desa_key})
    ON CREATE SET
        d.nama = row.desa,
        d.nama_normalized = row.desa_normalized

    MERGE (a:Alamat {key: row.alamat_key})
    ON CREATE SET
        a.nama = row.alamat,
        a.nama_normalized = row.alamat_normalized

    MERGE (s:SPPG {id: row.id})
    SET
        s.nama = row.nama_sppg,
        s.nama_normalized = row.nama_normalized,
        s.alamat = row.alamat,
        s.alamat_normalized = row.alamat_normalized,
        s.provinsi_normalized = row.provinsi_normalized,
        s.kabupaten_normalized = row.kabupaten_normalized,
        s.kecamatan_normalized = row.kecamatan_normalized,
        s.desa_normalized = row.desa_normalized

    // ==========================================
    // PEMBUATAN RELASI DUA ARAH UNTUK GRAPHRAG
    // ==========================================
    
    // 1. Relasi Provinsi <-> Kabupaten
    MERGE (p)-[:MEMILIKI_KABUPATEN]->(kk)
    MERGE (kk)-[:BAGIAN_DARI_PROVINSI]->(p)

    // 2. Relasi Kabupaten <-> Kecamatan
    MERGE (kk)-[:MEMILIKI_KECAMATAN]->(k)
    MERGE (k)-[:BAGIAN_DARI_KABUPATEN]->(kk)

    // 3. Relasi Kecamatan <-> Desa
    MERGE (k)-[:MEMILIKI_DESA]->(d)
    MERGE (d)-[:BAGIAN_DARI_KECAMATAN]->(k)

    // 4. Relasi Desa <-> SPPG
    MERGE (d)-[:MEMILIKI_SPPG]->(s)
    MERGE (s)-[:BERADA_DI_DESA]->(d)

    // 5. Relasi SPPG <-> Alamat
    MERGE (s)-[:MEMILIKI_ALAMAT]->(a)
    MERGE (a)-[:ALAMAT_DARI_SPPG]->(s)
    """

    with driver.session() as session:
        session.run(query, rows=rows)


def import_csv(csv_path: str, batch_size: int = 500):
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {csv_path}")

    seen_ids = set()
    rows = []
    total = 0
    duplicate_count = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for index, raw_row in enumerate(reader, start=1):
            row = transform_row(raw_row, fallback_id=index)

            if not row["id"]:
                continue

            # Menghilangkan duplicate berdasarkan ID SPPG
            if row["id"] in seen_ids:
                duplicate_count += 1
                continue

            seen_ids.add(row["id"])
            rows.append(row)

            if len(rows) >= batch_size:
                import_batch(rows)
                total += len(rows)
                print(f"Imported: {total}")
                rows = []

    if rows:
        import_batch(rows)
        total += len(rows)

    print(f"Total data diimport: {total}")
    print(f"Duplicate yang dilewati: {duplicate_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Pemakaian: python -m app.etl "
            "data/data_sppg.csv"
        )
        sys.exit(1)

    create_constraints()
    import_csv(sys.argv[1])