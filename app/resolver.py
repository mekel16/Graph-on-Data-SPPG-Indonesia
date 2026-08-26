from typing import Optional

from app.db import driver
from app.normalize import normalize_text


def resolve_districts(
    kecamatan: str,
    kabupaten_kota: Optional[str] = None,
    provinsi: Optional[str] = None,
) -> list[dict]:
    query = """
    MATCH (p:Provinsi)-[:MEMILIKI]->(kk:KabupatenKota)
          -[:MEMILIKI]->(k:Kecamatan)
          -[:MEMILIKI]->(d:Desa)
    WHERE k.nama_normalized = $kecamatan
      AND (
          $kabupaten_kota IS NULL
          OR kk.nama_normalized = $kabupaten_kota
      )
      AND (
          $provinsi IS NULL
          OR p.nama_normalized = $provinsi
      )
    RETURN
        p.nama AS provinsi,
        p.nama_normalized AS provinsi_normalized,
        kk.nama AS kabupaten_kota,
        kk.nama_normalized AS kabupaten_kota_normalized,
        k.nama AS kecamatan,
        k.nama_normalized AS kecamatan_normalized
    ORDER BY p.nama, kk.nama, k.nama
    """

    params = {
        "kecamatan": normalize_text(kecamatan),
        "kabupaten_kota": (
            normalize_text(kabupaten_kota)
            if kabupaten_kota
            else None
        ),
        "provinsi": (
            normalize_text(provinsi)
            if provinsi
            else None
        ),
    }

    with driver.session() as session:
        result = session.run(query, params)
        return [record.data() for record in result]


def resolve_city(
    kabupaten_kota: str,
    provinsi: Optional[str] = None,
) -> list[dict]:
    query = """
    MATCH (p:Provinsi)-[:MEMILIKI]->(kk:KabupatenKota)
    WHERE kk.nama_normalized = $kabupaten_kota
      AND (
          $provinsi IS NULL
          OR p.nama_normalized = $provinsi
      )
    RETURN
        p.nama AS provinsi,
        p.nama_normalized AS provinsi_normalized,
        kk.nama AS kabupaten_kota,
        kk.nama_normalized AS kabupaten_kota_normalized
    ORDER BY p.nama, kk.nama
    """

    params = {
        "kabupaten_kota": normalize_text(kabupaten_kota),
        "provinsi": (
            normalize_text(provinsi)
            if provinsi
            else None
        ),
    }

    with driver.session() as session:
        result = session.run(query, params)

        return [record.data() for record in result]