# Penerapan GraphRAG pada Data SPPG Se-Indonesia

<p align="left">
  <img src="https://img.shields.io/badge/Ubuntu-E95420?style=flat&logo=ubuntu&logoColor=white" alt="Ubuntu" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Neo4j-008CC1?style=flat&logo=neo4j&logoColor=white" alt="Neo4j" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white" alt="Ollama" />
</p>

## Inti dari projek ini adalah bahwa bagaimana bisa mendapatkan konteks _natural language_ dari data tabular bukan dengan _vector search_. Tapi dengan pendekatan graf

<div align="center">

<div style="overflow-x: auto; padding: 10px 0;">

<table>
<tr>
<td align="center" valign="top">

### 01 · Tabular Data

<img src="https://github.com/user-attachments/assets/35bd9f8f-f0ff-4a17-9e32-e3cc7387062f" alt="Tabular Data and Architecture" style="max-width: 450px; width: 100%; height: auto;" />

<p>
Dibentuk menjadi graph dahulu dengan relasi seperti di gambar
</p>

</td>
</tr>

<tr>
<td align="center">

### ↓

</td>
</tr>

<tr>
<td align="center" valign="top">

### 02 · Graph Representation

<img src="https://github.com/user-attachments/assets/40e0eaa8-386b-432f-a472-d20050bd71d2" alt="Graph Visualization" style="max-width: 450px; width: 100%; height: auto;" />

<p>
Lalu menghasilkan data graph yang tersimpan di database neo4j
</p>

</td>
</tr>

<tr>
<td align="center">

### ↓

</td>
</tr>

<tr>
<td align="center" valign="top">

### 03 · Natural Language Generation

<img src="https://github.com/user-attachments/assets/d71f7b77-4de2-45b3-9be1-9a587b0115fb" alt="Natural Language Output" style="max-width: 450px; width: 100%; height: auto;" />

<p>
dengan menerapkan model ollama dan _text to chyper_ maka akan diberikan hasil dalam natural language seperti pada gambar di bawah
</p>

</td>
</tr>
</table>

</div>

</div>

---

## Struktur Projek

```
sppg_graphrag/
├── app/
│   ├── main.py              # FastAPI entry point, 3 endpoints
│   ├── config.py             # Pydantic Settings dari .env
│   ├── db.py                 # Neo4j driver singleton + retry logic
│   ├── etl.py                # CSV → Neo4j graph pipeline
│   ├── llm_router.py         # Intent classification via LLM
│   ├── text_to_cypher.py     # Natural language → Cypher query
│   ├── queries.py            # Predefined Cypher + executor
│   ├── resolver.py           # Entity resolution (disambiguation)
│   ├── answer_generator.py   # Format jawaban jadi natural language
│   ├── normalize.py          # Normalisasi teks (prefix, spasi, dll)
│   └── observability.py      # Query logging ke SQLite
├── data/
│   ├── data_sppg.csv         # ~27.000 records SPPG se-Indonesia
│   └── eda.ipynb             # Exploratory data analysis
├── schema.cypher             # DDL constraints + indexes Neo4j
├── cli_chat.py               # Terminal chat client
├── requirements.txt
└── .env
```

---

## Kenapa Graph?

Pertanyaan klasik: kenapa ga pake vector search aja?

Karena data SPPG ini punya **struktur hierarki** yang jelas — ada provinsi, kabupaten/kota, kecamatan, desa, sampai lokasi SPPG-nya. Kalau di-vectorize, kita cuma bisa cari "kemiripan" antar dokumen, tapi kita ga bisa **traversal** relasi hierarkis itu.

Contohnya, kalau user tanya *"berapa banyak SPPG di Jawa Tengah?"*, vector search cuma bisa cari chunk teks yang mirip. Tapi dengan graph, kita bisa **langsung traversel** dari node `Provinsi` → `KabupatenKota` → `Kecamatan` → `Desa` → `SPPG` dan hitung semuanya secara struktural.

Intinya: **graph memberikan konteks yang lebih kaya untuk data yang punya relasi hierarkis.**

---

## Arsitektur

```
User (Bahasa Indonesia)
        │
        ▼
┌──────────────────────┐
│   FastAPI Server     │  POST /ask
│     (main.py)        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   LLM Intent Router  │  Klasifikasi intent dari pertanyaan user
│   (llm_router.py)    │  → 8 jenis intent
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────────────┐
│ Predefined│  │  Text-to-Cypher  │  Fallback untuk intent
│  Queries  │  │ (text_to_cypher  │  yang ga dikenali
│(queries.py)│ │      .py)       │
└─────┬────┘  └────────┬─────────┘
      │                │
      ▼                ▼
┌──────────────────────┐
│      Neo4j Graph     │  ~27.000+ node SPPG
│   (AuraDB Cloud)     │  5 tipe node, 10 relasi
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Answer Generator    │  Format jawaban jadi
│ (answer_generator.py)│  natural language
└──────────────────────┘
```

---

## Schema Graph

Node dan relasi yang dibangun dari data CSV yang terbentuk adalah _unirected graph_ artinya ada relasi bolak balik tiap node (simpul):

```
(:Provinsi)
    │
    ├──[:MEMILIKI_KABUPATEN]──► (:KabupatenKota)
    │       ◄──[:BAGIAN_DARI_PROVINSI]──┘
    │
    │       ├──[:MEMILIKI_KECAMATAN]──► (:Kecamatan)
    │       │       ◄──[:BAGIAN_DARI_KABUPATEN]──┘
    │       │
    │       │       ├──[:MEMILIKI_DESA]──► (:Desa)
    │       │       │       ◄──[:BAGIAN_DARI_KECAMATAN]──┘
    │       │       │
    │       │       │       ├──[:MEMILIKI_SPPG]──► (:SPPG)
    │       │       │       │       ◄──[:BERADA_DI_DESA]──┘
    │       │       │       │
    │       │       │       ├──[:MEMILIKI_ALAMAT]──► (:Alamat)
    │       │       │       │       ◄──[:ALAMAT_DARI_SPPG]──┘
```

Semua relasi bersifat **bidirectional** supaya traversal bisa dilakukan dari arah manapun.

---

## Intent yang Didukung

Sistem ini bisa mengenali 8 jenis intent dari pertanyaan user dalam Bahasa Indonesia:

| Intent | Contoh Pertanyaan |
|--------|-------------------|
| `count_sppg_by_kecamatan` | "Berapa SPPG di Kecamatan X?" |
| `list_sppg_by_kecamatan` | "SPPG apa saja di Kecamatan X?" |
| `count_sppg_by_kabupaten` | "Berapa SPPG di Kabupaten Y?" |
| `ranking_sppg_by_kabupaten` | "Kabupaten mana yang paling banyak SPPG-nya?" |
| `search_sppg_by_desa` | "Cari SPPG di Desa Z" |
| `search_sppg_by_alamat` | "SPPG yang alamatnya di Jl. ABC" |
| `summary_by_province` | "Ringkasan SPPG di Jawa Barat" |
| `unknown` | Pertanyaan di luar intent di atas → fallback ke text-to-cypher |

---

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | FastAPI + Uvicorn |
| Graph Database | Neo4j (AuraDB) |
| LLM | Ollama (Qwen 2.5 7B) |
| LLM Client | OpenAI Python SDK (custom base_url) |
| Data Validation | Pydantic + pydantic-settings |
| Observability | SQLite (query logging) |
| Data Format | CSV (~27.000 records SPPG) |

---

## Instalasi

### Prasyarat

- Python 3.10+
- Neo4j instance (local atau AuraDB)
- Ollama terinstall dan model `qwen2.5:7b` sudah di-pull

```bash
ollama pull qwen2.5:7b
```

### Setup

```bash
# Clone repo
git clone https://github.com/<username>/sppg_graphrag.git
cd sppg_graphrag

# Buat virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# atau .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy dan isi .env
cp .env.example .env
```

### Konfigurasi `.env`

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b

ENVIRONMENT=development
```

### Import Data

```bash
# Jalankan ETL pipeline untuk import CSV ke Neo4j
python -m app.etl data/data_sppg.csv
```

### Jalankan Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/` | Status server |
| `GET` | `/health` | Health check |
| `POST` | `/ask` | Kirim pertanyaan dalam Bahasa Indonesia |

### Contoh Request

```bash
curl -X POST http://127.0.0.1:8010/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Berapa jumlah SPPG di Jawa Tengah?"}'
```

### Contoh Response

```json
{
  "answer": "Berdasarkan data graph, terdapat 2.847 SPPG yang tersebar di seluruh kabupaten/kota di Jawa Tengah...",
  "intent": "summary_by_province",
  "cypher": "MATCH (p:Provinsi {nama: 'JAWA TENGAH'})-[:MEMILIKI_KABUPATEN]->(k)...",
  "duration_ms": 1234
}
```

---

## CLI Chat

Selain API, ada juga client terminal buat ngobrol langsung:

```bash
python cli_chat.py
```

```
╭──────────────────────────────────────────╮
│        SPPG GraphRAG - CLI Chat         │
│  Ketik pertanyaan atau 'keluar' untuk   │
│              keluar                      │
╰──────────────────────────────────────────╯

Pertanyaan: berapa SPPG di Kabupaten Bandung?

Jawaban: ...
Intent: count_sppg_by_kabupaten
```

---

## Observability

Setiap query yang masuk dicatat ke SQLite (`observability.db`) dengan field:

- `question` — pertanyaan dari user
- `intent` — intent yang terdeteksi
- `parameters` — parameter ekstraksi entity
- `cypher` — query Cypher yang dijalankan
- `result` — hasil dari Neo4j
- `duration_ms` — waktu eksekusi
- `status` — success / error

Ini berguna buat debug dan monitor query mana yang sering fail atau lambat.

---

## Deep Dive: ETL Pipeline

ETL (`app/etl.py`) convert data CSV jadi graph di Neo4j. Prosesnya:

```
CSV Reader
    │
    ▼
Row Transformer
    │  - Normalisasi nama (hapus prefix "Kec.", "Kab.", dll)
    │  - Build hierarchical key: PROVINSI|KABUPATEN|KECAMATAN|DESA
    │  - Deduplicate by SPPG ID
    │
    ▼
Batch Importer (UNWIND)
    │  - Create nodes: Provinsi, KabupatenKota, Kecamatan, Desa, SPPG, Alamat
    │  - Create relasi: MEMILIKI_* dan BAGIAN_DARI_*
    │  - Dedup pakai MERGE (bukan CREATE)
    │
    ▼
Neo4j Database (~27.000+ SPPG nodes)
```

Yang menarik di sini:
- Pakai **batch import** pake `UNWIND` bukan satu-satu, supaya import 27k data ga lambat
- **Deduplication** via `MERGE` — kalau data CSV ada duplikat, ga bakal double create di graph
- **Hierarchical key** — setiap node punya key unik berdasarkan path hierarkinya, misal `JAWA TENGAH|KEBUMEN|BUAYAN`

Jalankan sendiri:

```bash
python -m app.etl data/data_sppg.csv
```

---

## Deep Dive: Intent Classification + Text-to-Cypher

Ini bagian yang paling interesting menurut gue. Sistemnya pakai **2 jalur** buat handle pertanyaan user:

### Jalur 1: Intent Router (`llm_router.py`)

User nanya → LLM classify ke salah satu dari 8 intent → query predefined yang sudah optimised dijalankan.

```
"Berapa SPPG di Kecamatan Buayan?"
        │
        ▼
┌─────────────────────────┐
│  LLM Intent Classifier  │
│                         │
│  Output: {              │
│    "intent": "count_sppg│_by_kecamatan",
│    "kecamatan": "buayan" │
│  }                      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Predefined Cypher     │
│   MATCH (k:Kecamatan    │
│     {nama: 'buayan'})   │
│   -[:MEMILIKI_SPPG]->   │
│   (s:SPPG)              │
│   RETURN count(s)       │
└─────────────────────────┘
```

Kelebihan jalur ini: **predictable** — query-nya sudah di-test dan optimised, jarang error.

### Jalur 2: Text-to-Cypher Fallback (`text_to_cypher.py`)

Kalau intent ga dikenali (masuk `unknown`), LLM generate Cypher query mentah dari natural language.

```
"Provinsi mana yang paling sedikit SPPG-nya?"
        │
        ▼
┌─────────────────────────────┐
│  Text-to-Cypher Generator   │
│                             │
│  Prompt includes:           │
│  - Schema graph (node/rel)  │
│  - Instruksi: READ only      │
│  - Contoh Cypher            │
│                             │
│  Output:                    │
│  MATCH (p:Provinsi)         │
│  -[:MEMILIKI_KABUPATEN]->   │
│  (k:KabupatenKota)          │
│  WITH p, count(k) AS total  │
│  RETURN p.nama, total       │
│  ORDER BY total ASC LIMIT 5 │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│     Cypher Validator        │
│  - Reject CREATE/MERGE/     │
│    DELETE/DROP/SET          │
│  - Hanya boleh MATCH+RETURN │
└─────────────────────────────┘
```

**Security concern**: text-to-cypher itu powerful tapi berbahaya. Untuk itu ada `validate_cypher()` yang **reject** semua write operations — jadi user ga bisa inject Cypher buat hapus data.

---

## Deep Dive: Entity Resolution

Salah satu challenge terbesar: **nama kecamatan/kabupaten yang sama di beberapa provinsi**.

Contoh: "Kecamatan Sukamaju" ada di Jawa Barat DAN di Jawa Tengah. Kalau user cuma bilang "SPPG di Kecamatan Sukamaju", sistem harus **disambiguate** dulu.

```
"Berapa SPPG di Kecamatan Sukamaju?"
        │
        ▼
┌─────────────────────────────┐
│    Entity Resolver          │
│    (resolver.py)            │
│                             │
│  Query: MATCH (k:Kecamatan  │
│    {nama: 'sukamaju'})      │
│  RETURN k, provinsi         │
│                             │
│  Hasil: 2 kandidat!         │
│  1. Sukamaju - Jawa Barat   │
│  2. Sukamaju - Jawa Tengah  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Disambiguation Prompt      │
│  "Ada beberapa kecamatan    │
│   dengan nama yang sama.    │
│   Maksud kamu yang mana?"   │
└─────────────────────────────┘
```

Ini penting karena **data Indonesia punya banyak nama daerah yang duplikat** antar provinsi. Tanpa disambiguation, hasil query bakal salah.

---

## Deep Dive: Observability & Retry

### Query Logging

Setiap request dicatat ke SQLite. Ini penting banget buat:
- **Debugging** — kalau ada query yang error, bisa trace dari log
- **Performance monitoring** — track berapa lama tiap query dieksekusi
- **Pattern analysis** — pertanyaan apa yang paling sering ditanya

### Retry Logic

Neo4j query kadang fail karena:
- `SessionExpired` — session timeout
- `TransientError` — sementara ga bisa diakses
- `ServiceUnavailable` — server down

Sistem retry otomatis **3 kali** dengan exponential backoff (1 detik → 2 detik → 4 detik).

---

## Schema Constraints & Indexes

File `schema.cypher` mendefinisikan struktur database sebelum data diimport:

```cypher
// Unique constraints — ga boleh ada duplikat
CREATE CONSTRAINT sppg_id_unique IF NOT EXISTS
FOR (s:SPPG) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT provinsi_nama_unique IF NOT EXISTS
FOR (p:Provinsi) REQUIRE p.nama IS UNIQUE;

CREATE CONSTRAINT kabupaten_nama_unique IF NOT EXISTS
FOR (k:KabupatenKota) REQUIRE k.key IS UNIQUE;

// Performance indexes — biar query ga full scan
CREATE INDEX kecamatan_nama_index IF NOT EXISTS
FOR (k:Kecamatan) ON (k.nama);

CREATE INDEX desa_nama_index IF NOT EXISTS
FOR (d:Desa) ON (d.nama);
```

Ini penting karena:
- **Unique constraint** mencegah duplikat data masuk ke graph
- **Index** bikin query traversal lebih cepat (ga perlu scan semua node)

---

## Prompt Engineering

Salah satu aspek yang sering di-skip: prompt design. Di projek ini ada 3 prompt utama:

### 1. Intent Classification Prompt
LLM dikasih daftar 8 intent + deskripsi + contoh, lalu diminta return JSON. Kuncinya: **jelas dan spesifik** — kalau intent-nya ambigu, klasifikasi bakal sering salah.

### 2. Text-to-Cypher Prompt
LLM dikasih **schema graph** (semua node dan relasi yang ada), instruksi untuk READ, dan beberapa contoh query. Ini penting biar LLM ga generate CREATE/DELETE.

### 3. Answer Generator Prompt
Buat summary_by_province, LLM diminta analisis data numerik dan generate insight dalam Bahasa Indonesia — bukan cuma return angka mentah.

---

## Normalisasi & Text Processing

Data Indonesia itu **chaos**. Nama daerah ditulis dengan banyak variasi:

| Asli di CSV | Setelah Normalisasi |
|-------------|---------------------|
| `Kec. Buayan` | `buayan` |
| `KABUPATEN KEBUMEN` | `kebumen` |
| `Kota Bandung` | `bandung` |
| `PROVINSI JAWA TENGAH` | `jawa tengah` |

`normalize.py` handle semua ini dengan:
1. **Strip prefix** — hapus "Kec.", "Kab.", "Kota", "Provinsi", dll
2. **Lowercase** — standarisasi casing
3. **Strip whitespace** — hapus spasi berlebih
4. **Hapus tanda baca** — biar matching lebih robust

---

## Error Handling

Sistem punya beberapa layer pertahanan:

```
User Query
    │
    ├─► Intent Classification gagal?
    │       → Fallback ke text-to-cypher
    │
    ├─► Text-to-Cypher generate query invalid?
    │       → Return error message ke user
    │
    ├─► CypherValidator detect write operation?
    │       → Reject query, return error
    │
    ├─► Neo4j query timeout/error?
    │       → Retry 3x dengan backoff
    │       → Kalau masih gagal, return error
    │
    └─► Entity resolution ambiguous?
            → Tanya balik ke user
```

Layered defense begini penting biar sistem ga gampang crash atau return data yang salah.

---

## Graph and natural language

Contoh konkret: *"Berapa SPPG di tiap kabupaten di Jawa Tengah?"*

- **Graph**: `MATCH (p:Provinsi {nama:'JAWA TENGAH'})-[:MEMILIKI_KABUPATEN]->(k)-[:MEMILIKI_KECAMATAN]->()-[:MEMILIKI_DESA]->()-[:MEMILIKI_SPPG]->(s) RETURN k.nama, count(s)` 

---

## Performance

Beberapa optimasi yang dilakukan:

- **Batch import** — `UNWIND` buat bulk insert, bukan satu-satu
- **MERGE bukan CREATE** — deduplication di level database
- **Unique constraints** — mencegah duplikat data masuk
- **Indexes** — pada field yang sering di-query (nama, key)
- **Retry with backoff** — handle transient errors tanpa crash

Dengan optimasi ini, import 27k data selesai dalam hitungan menit, bukan jam.

---

## SaYA tertarik dengan GRaph Rag sehingga mencoba memahami ini dahulu

Beberapa hal yang menurut gue worth untuk ditunjukin:

1. **Graph over Vector** — menunjukkan pemahaman kapan pakai graph vs vector search, bukan asal pakai RAG
2. **Text-to-Cypher** — implementasi LLM yang generate query Cypher langsung dari natural language, bukan cuma prompt-response
3. **Intent Classification** — custom router yang classify pertanyaan user ke intent spesifik sebelum query, supaya lebih akurat
4. **ETL Pipeline** — transformasi data tabular jadi graph dengan 5 tipe node dan 10 relasi bidirectional
5. **Observability** — logging query ke SQLite buat monitoring dan debugging
6. **Indonesian-first** — seluruh UI, prompt, dan data berbahasa Indonesia — menunjukkan kemampuan bikin sistem NLP untuk bahasa lokal
7. **Entity Resolution** — disambiguation otomatis untuk nama daerah yang ambigu antar provinsi
8. **Security** — Cypher validator yang reject write operations dari text-to-cypher

---

## Roadmap / Future Work

Beberapa hal yang bisa dikembangkan lagi:

- [ ] **Vector search** sebagai hybrid — gabungin graph traversal DAN vector similarity buat pertanyaan yang lebih fuzzy
- [ ] **Streaming response** — kasih response token-by-token biar user ga nunggu lama
- [ ] **Multi-turn conversation** — simpan konteks percakapan sebelumnya
- [ ] **Web UI** — frontend pake Streamlit/Gradio biar lebih user-friendly
- [ ] **Bulk import** — parallel processing buat import data yang lebih cepat
- [ ] **More intent types** — misalnya "SPPG terdekat dari lokasi X" pakai spatial query

---

## Quick Start

```bash
# 1. Setup
git clone https://github.com/<username>/sppg_graphrag.git && cd sppg_graphrag
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Jalankan Ollama
ollama pull qwen2.5:7b

# 3. Import data ke Neo4j (pastikan Neo4j udah jalan)
python -m app.etl data/data_sppg.csv

# 4. Jalankan server
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload

# 5. Test
curl -X POST http://127.0.0.1:8010/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Berapa SPPG di Jawa Tengah?"}'
```

---

## Data Source

Data SPPG diambil dari sumber publik pemerintah Indonesia. Dataset berisi informasi lokasi Sentra Pelayanan Papa Gracia (SPPG) di seluruh provinsi Indonesia, termasuk:

- Nama Provinsi
- Kabupaten/Kota
- Kecamatan
- Kelurahan/Desa
- Alamat lengkap SPPG
- Nama SPPG

---
