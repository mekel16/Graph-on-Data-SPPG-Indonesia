import logging
import time
from typing import Optional

from app.db import RETRYABLE_ERRORS, driver

log = logging.getLogger(__name__)

MAX_RETRIES = 3


COUNT_BY_KECAMATAN = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
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
    count(DISTINCT s) AS jumlah,
    collect(DISTINCT {
        provinsi: p.nama,
        kabupaten_kota: kk.nama,
        kecamatan: k.nama
    }) AS wilayah
"""


LIST_BY_KECAMATAN = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
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
    s.id AS id,
    s.nama AS nama,
    s.alamat AS alamat,
    d.nama AS desa,
    k.nama AS kecamatan,
    kk.nama AS kabupaten_kota,
    p.nama AS provinsi
ORDER BY s.nama
LIMIT $limit
"""


COUNT_BY_KABUPATEN = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE kk.nama_normalized = $kabupaten_kota
  AND (
      $provinsi IS NULL
      OR p.nama_normalized = $provinsi
  )
RETURN
    count(DISTINCT s) AS jumlah,
    collect(DISTINCT {
        provinsi: p.nama,
        kabupaten_kota: kk.nama
    }) AS wilayah
"""


RANKING_KABUPATEN = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE $provinsi IS NULL
   OR p.nama_normalized = $provinsi
RETURN
    p.nama AS provinsi,
    kk.nama AS kabupaten_kota,
    count(DISTINCT s) AS jumlah_sppg
ORDER BY jumlah_sppg DESC
LIMIT $limit
"""


SEARCH_BY_DESA = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE d.nama_normalized = $desa
  AND (
      $kecamatan IS NULL
      OR k.nama_normalized = $kecamatan
  )
  AND (
      $kabupaten_kota IS NULL
      OR kk.nama_normalized = $kabupaten_kota
  )
RETURN
    s.id AS id,
    s.nama AS nama,
    s.alamat AS alamat,
    d.nama AS desa,
    k.nama AS kecamatan,
    kk.nama AS kabupaten_kota,
    p.nama AS provinsi
ORDER BY s.nama
LIMIT $limit
"""


SEARCH_BY_ALAMAT = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE s.alamat_normalized CONTAINS $keyword
RETURN
    s.id AS id,
    s.nama AS nama,
    s.alamat AS alamat,
    d.nama AS desa,
    k.nama AS kecamatan,
    kk.nama AS kabupaten_kota,
    p.nama AS provinsi
ORDER BY s.nama
LIMIT $limit
"""

SUMMARY_BY_PROVINCE = """
MATCH (p:Provinsi)
WHERE p.nama_normalized = $provinsi

CALL {
    WITH p
    MATCH (p)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
    RETURN count(DISTINCT kk) AS total_kabupaten
}

CALL {
    WITH p
    MATCH (p)-[:MEMILIKI_KABUPATEN]->(:KabupatenKota)
          -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
    RETURN count(DISTINCT k) AS total_kecamatan
}

CALL {
    WITH p
    MATCH (p)-[:MEMILIKI_KABUPATEN]->(:KabupatenKota)
          -[:MEMILIKI_KECAMATAN]->(:Kecamatan)
          -[:MEMILIKI_DESA]->(d:Desa)
    RETURN count(DISTINCT d) AS total_desa
}

CALL {
    WITH p
    MATCH (p)-[:MEMILIKI_KABUPATEN]->(:KabupatenKota)
          -[:MEMILIKI_KECAMATAN]->(:Kecamatan)
          -[:MEMILIKI_DESA]->(:Desa)
          -[:MEMILIKI_SPPG]->(s:SPPG)
    RETURN count(DISTINCT s) AS total_sppg
}

RETURN
    p.nama AS provinsi,
    total_kabupaten,
    total_kecamatan,
    total_desa,
    total_sppg
"""


TOP_KABUPATEN_BY_PROVINCE = """
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE p.nama_normalized = $provinsi
RETURN
    kk.nama AS kabupaten_kota,
    count(DISTINCT s) AS jumlah_sppg
ORDER BY jumlah_sppg DESC
LIMIT $limit
"""


def summary_by_province(provinsi: str) -> dict:
    rows = run_query(
        SUMMARY_BY_PROVINCE,
        {
            "provinsi": provinsi,
        },
    )

    if not rows:
        return {
            "found": False,
            "summary": None,
        }

    return {
        "found": True,
        "summary": rows[0],
    }


def top_kabupaten_by_province(
    provinsi: str,
    limit: int = 10,
) -> list[dict]:
    return run_query(
        TOP_KABUPATEN_BY_PROVINCE,
        {
            "provinsi": provinsi,
            "limit": limit,
        },
    )


def run_query(query: str, params: dict) -> list[dict]:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with driver.session() as session:
                result = session.run(query, params)
                return [record.data() for record in result]
        except RETRYABLE_ERRORS as exc:
            last_error = exc
            delay = attempt * 2
            log.warning(
                "Query attempt %d/%d failed: %s. "
                "Retrying in %ds...",
                attempt,
                MAX_RETRIES,
                exc,
                delay,
            )
            time.sleep(delay)

    raise last_error


def count_by_kecamatan(
    kecamatan: str,
    kabupaten_kota: Optional[str] = None,
    provinsi: Optional[str] = None,
) -> dict:
    rows = run_query(
        COUNT_BY_KECAMATAN,
        {
            "kecamatan": kecamatan,
            "kabupaten_kota": kabupaten_kota,
            "provinsi": provinsi,
        },
    )

    return rows[0] if rows else {
        "jumlah": 0,
        "wilayah": [],
    }


def list_by_kecamatan(
    kecamatan: str,
    kabupaten_kota: Optional[str] = None,
    provinsi: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    return run_query(
        LIST_BY_KECAMATAN,
        {
            "kecamatan": kecamatan,
            "kabupaten_kota": kabupaten_kota,
            "provinsi": provinsi,
            "limit": limit,
        },
    )


def count_by_kabupaten(
    kabupaten_kota: str,
    provinsi: Optional[str] = None,
) -> dict:
    rows = run_query(
        COUNT_BY_KABUPATEN,
        {
            "kabupaten_kota": kabupaten_kota,
            "provinsi": provinsi,
        },
    )

    return rows[0] if rows else {
        "jumlah": 0,
        "wilayah": [],
    }


def ranking_kabupaten(
    provinsi: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    return run_query(
        RANKING_KABUPATEN,
        {
            "provinsi": provinsi,
            "limit": limit,
        },
    )


def search_by_desa(
    desa: str,
    kecamatan: Optional[str] = None,
    kabupaten_kota: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    return run_query(
        SEARCH_BY_DESA,
        {
            "desa": desa,
            "kecamatan": kecamatan,
            "kabupaten_kota": kabupaten_kota,
            "limit": limit,
        },
    )


def search_by_alamat(
    keyword: str,
    limit: int = 100,
) -> list[dict]:
    return run_query(
        SEARCH_BY_ALAMAT,
        {
            "keyword": keyword,
            "limit": limit,
        },
    )