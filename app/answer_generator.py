import json

from openai import OpenAI

from app.config import settings


client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)


def generate_province_summary(
    province_data: dict,
) -> str:
    prompt = f"""
Anda adalah analis data SPPG.

Buat analisis singkat mengenai kondisi SPPG
berdasarkan data berikut:

{json.dumps(province_data, ensure_ascii=False, indent=2)}

Aturan:
- Gunakan hanya angka yang tersedia.
- Jangan membuat angka baru.
- Jangan mengarang fakta.
- Gunakan bahasa Indonesia.
- Jangan menambahkan kepanjangan apapun pada SPPG cukup tuliskan SPPG saja
- Jika data tidak cukup, katakan data belum tersedia.

Format:
Gambaran umum:
...

Distribusi:
...

Kabupaten dengan jumlah terbanyak:
...

Catatan:
...
"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Anda adalah analis data yang "
                    "tidak boleh mengarang angka."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content