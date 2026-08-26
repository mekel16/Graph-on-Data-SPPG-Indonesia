import json
import re
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from app.config import settings


client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


class CypherResponse(BaseModel):
    cypher: str
    params: dict[str, Any] = {}


GRAPH_SCHEMA = """
Graph database Neo4j memiliki schema berikut:

Node:
(:Provinsi)
  - key (unique)
  - nama
  - nama_normalized

(:KabupatenKota)
  - key (unique)
  - nama
  - nama_normalized

(:Kecamatan)
  - key (unique)
  - nama
  - nama_normalized

(:Desa)
  - key (unique)
  - nama
  - nama_normalized

(:SPPG)
  - id (unique)
  - nama
  - nama_normalized
  - alamat
  - alamat_normalized
  - provinsi_normalized
  - kabupaten_normalized
  - kecamatan_normalized
  - desa_normalized
  - embedding (vector, dimensi 768)

(:Alamat)
  - key (unique)
  - nama
  - nama_normalized

Relationship (arah ke bawah):
(:Provinsi)-[:MEMILIKI_KABUPATEN]->(:KabupatenKota)
(:KabupatenKota)-[:MEMILIKI_KECAMATAN]->(:Kecamatan)
(:Kecamatan)-[:MEMILIKI_DESA]->(:Desa)
(:Desa)-[:MEMILIKI_SPPG]->(:SPPG)
(:SPPG)-[:MEMILIKI_ALAMAT]->(:Alamat)

Relationship (arah ke atas):
(:KabupatenKota)-[:BAGIAN_DARI_PROVINSI]->(:Provinsi)
(:Kecamatan)-[:BAGIAN_DARI_KABUPATEN]->(:KabupatenKota)
(:Desa)-[:BAGIAN_DARI_KECAMATAN]->(:Kecamatan)
(:SPPG)-[:BERADA_DI_DESA]->(:Desa)
(:Alamat)-[:ALAMAT_DARI_SPPG]->(:SPPG)

Contoh query yang benar:
MATCH (p:Provinsi)-[:MEMILIKI_KABUPATEN]->(kk:KabupatenKota)
      -[:MEMILIKI_KECAMATAN]->(k:Kecamatan)
      -[:MEMILIKI_DESA]->(d:Desa)
      -[:MEMILIKI_SPPG]->(s:SPPG)
WHERE p.nama_normalized = $provinsi
RETURN s.nama, s.alamat, d.nama, k.nama, kk.nama
"""


def generate_cypher(question: str) -> CypherResponse:
    prompt = f"""
{GRAPH_SCHEMA}

Pertanyaan pengguna:
{question}

Buat query Cypher read-only.

Aturan wajib:
- Hanya boleh menggunakan MATCH, OPTIONAL MATCH, WHERE, WITH,
  RETURN, ORDER BY, SKIP, LIMIT.
- Dilarang menggunakan CREATE, MERGE, DELETE, SET, REMOVE, DROP,
  LOAD CSV, CALL, USE, SHOW, TERMINATE.
- Jangan menggunakan semicolon.
- Gunakan parameter Cypher.
- Untuk menghitung SPPG, gunakan count(DISTINCT s).
- Kembalikan JSON dengan format:
{{
  "cypher": "MATCH ... RETURN ...",
  "params": {{}}
}}
"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Anda adalah generator Cypher Neo4j "
                    "yang hanya menghasilkan query read-only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)

    result = CypherResponse(**data)
    validate_cypher(result.cypher)

    return result


def validate_cypher(cypher: str) -> None:
    """
    Validasi minimal sebelum query dikirim ke Neo4j.
    Tetap gunakan user Neo4j read-only untuk keamanan tambahan.
    """

    query = cypher.strip()

    if not query:
        raise ValueError("Cypher kosong.")

    if ";" in query:
        raise ValueError("Multiple statement tidak diizinkan.")

    forbidden_keywords = [
        "CREATE",
        "MERGE",
        "DELETE",
        "DETACH",
        "SET",
        "REMOVE",
        "DROP",
        "LOAD CSV",
        "CALL",
        "USE",
        "SHOW",
        "TERMINATE",
        "GRANT",
        "DENY",
        "REVOKE",
    ]

    upper_query = re.sub(r"\s+", " ", query.upper())

    for keyword in forbidden_keywords:
        if keyword in upper_query:
            raise ValueError(
                f"Keyword Cypher tidak diizinkan: {keyword}"
            )

    if not re.search(r"\bMATCH\b", upper_query):
        raise ValueError("Query harus memiliki MATCH.")

    if not re.search(r"\bRETURN\b", upper_query):
        raise ValueError("Query harus memiliki RETURN.")