import json
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.normalize import normalize_text


client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


class IntentResult(BaseModel):
    intent: str = Field(
        description="Jenis operasi yang akan dilakukan"
    )
    kecamatan: Optional[str] = None
    kabupaten_kota: Optional[str] = None
    provinsi: Optional[str] = None
    desa: Optional[str] = None
    keyword: Optional[str] = None
    limit: int = 100


SYSTEM_PROMPT = """
Anda adalah intent classifier untuk sistem data SPPG.

Tugas Anda adalah mengubah pertanyaan bahasa Indonesia menjadi JSON.

Intent yang tersedia:
1. count_sppg_by_kecamatan
2. list_sppg_by_kecamatan
3. count_sppg_by_kabupaten
4. ranking_sppg_by_kabupaten
5. search_sppg_by_desa
6. search_sppg_by_alamat
7. summary_by_province
8. unknown

Aturan:
- Jangan menjawab pertanyaan.
- Jangan menambahkan kepanjangan apapun dari SPPG 
- Hanya keluarkan JSON.
- Normalisasi nama wilayah menjadi huruf kecil.
- Buang prefix seperti kecamatan, kec., kabupaten, kab., provinsi.
- Jangan menebak nama wilayah yang tidak disebutkan.
- Jika pengguna meminta "berapa", gunakan intent count.
- Jika pengguna meminta "tampilkan", "daftar", atau "list",
  gunakan intent list.
- Jika pengguna meminta peringkat atau ranking,
  gunakan intent ranking.
- Jika pengguna bertanya "bagaimana kondisi", "gambaran",
  "ringkasan", "analisis", atau "situasi" suatu provinsi,
  gunakan intent summary_by_province.
- Jika pertanyaan menyebut "Kabupaten X", isi
  kabupaten_kota dengan "x".
- Jika pertanyaan menyebut "Kota X", isi
  kabupaten_kota dengan "x".
- Jika pertanyaan menyebut "Provinsi X", isi
  provinsi dengan "x".
- Jika pertanyaan hanya menyebut nama provinsi,
  masukkan nama tersebut ke field provinsi.

Contoh 1:

Pertanyaan:
"Ada berapa SPPG di Kecamatan Buayan, Kabupaten Kebumen?"

Output:
{
  "intent": "count_sppg_by_kecamatan",
  "kecamatan": "buayan",
  "kabupaten_kota": "kebumen",
  "provinsi": null,
  "desa": null,
  "keyword": null,
  "limit": 100
}

Contoh 2:

Pertanyaan:
"Bagaimana kondisi SPPG di Jawa Timur?"

Output:
{
  "intent": "summary_by_province",
  "kecamatan": null,
  "kabupaten_kota": null,
  "provinsi": "jawa timur",
  "desa": null,
  "keyword": null,
  "limit": 10
}

Contoh 3:

Pertanyaan:
"Berikan gambaran SPPG di Provinsi Jawa Tengah."

Output:
{
  "intent": "summary_by_province",
  "kecamatan": null,
  "kabupaten_kota": null,
  "provinsi": "jawa tengah",
  "desa": null,
  "keyword": null,
  "limit": 10
}
"""


def classify_question(question: str) -> IntentResult:
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    result = IntentResult(**data)

    if result.kecamatan:
        result.kecamatan = normalize_text(result.kecamatan)

    if result.kabupaten_kota:
        result.kabupaten_kota = normalize_text(
            result.kabupaten_kota
        )

    if result.provinsi:
        result.provinsi = normalize_text(result.provinsi)

    if result.desa:
        result.desa = normalize_text(result.desa)

    if result.keyword:
        result.keyword = normalize_text(result.keyword)

    result.limit = max(1, min(result.limit, 500))

    return result