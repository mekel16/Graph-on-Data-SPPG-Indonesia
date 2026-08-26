# Penerapan Graph pada Data SPPG Se-Indonesia

<p align="left">
  <img src="https://img.shields.io/badge/Ubuntu-E95420?style=flat&logo=ubuntu&logoColor=white" alt="Ubuntu" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Neo4j-008CC1?style=flat&logo=neo4j&logoColor=white" alt="Neo4j" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white" alt="Ollama" />
</p>

## Inti dari proyek ini adalah bagaimana mendapatkan konteks _natural language_ dari data tabular, bukan dengan _vector search_, melainkan dengan pendekatan graf

<div align="center">

<div style="overflow-x: auto; padding: 10px 0;">

<table>
<tr>
<td align="center" valign="top">

### 01 · Tabular Data

<img src="https://github.com/user-attachments/assets/fc07d989-c8ef-4cc3-9700-405de7802dca" alt="Tabular Data and Architecture" style="max-width: 450px; width: 100%; height: auto;" />

<p>
Dibentuk menjadi graf terlebih dahulu dengan relasi seperti pada gambar
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
dengan menerapkan model Ollama dan _text to cypher_ maka akan dihasilkan respons dalam bentuk natural language seperti pada gambar di atas
</p>

</td>
</tr>
</table>

</div>

</div>

---

## Struktur Proyek

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
│   ├── answer_generator.py   # Format jawaban menjadi natural language
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
│   LLM Intent Router  │  Klasifikasi intent dari pertanyaan pengguna
│   (llm_router.py)    │  → 8 jenis intent
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────────────┐
│ Predefined│  │  Text-to-Cypher  │  Fallback untuk intent
│  Queries  │  │ (text_to_cypher  │  yang tidak dikenali
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
│  Answer Generator    │  Format jawaban menjadi
│ (answer_generator.py)│  natural language
└──────────────────────┘
```

---

## Schema Graph

Node dan relasi yang dibangun dari data CSV yang terbentuk adalah _undirected graph_, artinya ada relasi bolak-balik tiap node (simpul):

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

Semua relasi bersifat **bidirectional** agar traversal dapat dilakukan dari arah mana pun.

---

## Intent yang Didukung

Sistem ini dapat mengenali 8 jenis _intent_ dari pertanyaan pengguna dalam Bahasa Indonesia:

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

- Python 3.10+
- Neo4j instance (local atau AuraDB)
- Ollama terinstal dan model `qwen2.5:7b` sudah di-pull

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

Selain API, terdapat juga klien terminal untuk berinteraksi secara langsung:

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

Ini berguna untuk melakukan debug dan memantau query mana yang sering mengalami kegagalan atau lambat.

---

## Deep Dive: ETL Pipeline

ETL (`app/etl.py`) mengonversi data CSV menjadi graf di Neo4j. Prosesnya:

```
CSV Reader
    │
    ▼
Row Transformer
    │  - Normalisasi nama (menghapus awalan "Kec.", "Kab.", dll)
    │  - Build hierarchical key: PROVINSI|KABUPATEN|KECAMATAN|DESA
    │  - Deduplikasi berdasarkan ID SPPG
    │
    ▼
Batch Importer (UNWIND)
    │  - Membuat node: Provinsi, KabupatenKota, Kecamatan, Desa, SPPG, Alamat
    │  - Membuat relasi: MEMILIKI_* dan BAGIAN_DARI_*
    │  - Deduplikasi menggunakan MERGE (bukan CREATE)
    │
    ▼
Neo4j Database (~27.000+ SPPG nodes)
```

_run_:

```bash
python -m app.etl data/data_sppg.csv
```

---

## Deep Dive: Intent Classification + Text-to-Cypher

Ini merupakan bagian yang paling menarik menurut penulis. Sistem ini menggunakan **2 jalur** untuk menangani pertanyaan pengguna:

### Jalur 1: Intent Router (`llm_router.py`)

Pengguna bertanya → LLM mengklasifikasikan ke salah satu dari 8 intent → query predefined yang sudah dioptimasi dijalankan.

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

Keunggulan jalur ini: **predictable** — query-nya sudah diuji dan dioptimasi, jarang mengalami error.

### Jalur 2: Text-to-Cypher Fallback (`text_to_cypher.py`)

Jika intent tidak dikenali (masuk `unknown`), LLM menghasilkan Cypher query mentah dari natural language.

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

**Security concern**: text-to-cypher merupakan fitur yang kuat namun berbahaya. Untuk itu terdapat `validate_cypher()` yang **menolak** semua operasi write — sehingga pengguna tidak dapat menyuntikkan Cypher untuk menghapus data.

---

## Deep Dive: Entity Resolution

Salah satu challenge terbesar: **nama kecamatan/kabupaten yang sama di beberapa provinsi**.

Contoh: "Kecamatan Sukamaju" ada di Jawa Barat dan di Jawa Tengah. Jika pengguna hanya menyebutkan "SPPG di Kecamatan Sukamaju", sistem harus melakukan **disambiguasi** terlebih dahulu.

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

Ini penting karena **data Indonesia memiliki banyak nama daerah yang duplikat** antar provinsi. Tanpa disambiguasi, hasil query akan salah.

---

## Deep Dive: Observability & Retry

### Query Logging

Setiap request dicatat ke SQLite. Ini sangat penting untuk:
- **Debugging** — kalau ada query yang error, bisa trace dari log
- **Performance monitoring** — track berapa lama tiap query dieksekusi
- **Pattern analysis** — pertanyaan apa yang paling sering ditanya

### Retry Logic

Neo4j query terkadang mengalami kegagalan karena:
- `SessionExpired` — session timeout
- `TransientError` — sementara tidak dapat diakses
- `ServiceUnavailable` — server tidak berfungsi

Sistem retry otomatis **3 kali** dengan exponential backoff (1 detik → 2 detik → 4 detik).

---

## Schema Constraints & Indexes

File `schema.cypher` mendefinisikan struktur database sebelum data diimport:

```cypher
// Unique constraints — tidak boleh ada duplikat
CREATE CONSTRAINT sppg_id_unique IF NOT EXISTS
FOR (s:SPPG) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT provinsi_nama_unique IF NOT EXISTS
FOR (p:Provinsi) REQUIRE p.nama IS UNIQUE;

CREATE CONSTRAINT kabupaten_nama_unique IF NOT EXISTS
FOR (k:KabupatenKota) REQUIRE k.key IS UNIQUE;

// Performance indexes — agar query tidak melakukan full scan
CREATE INDEX kecamatan_nama_index IF NOT EXISTS
FOR (k:Kecamatan) ON (k.nama);

CREATE INDEX desa_nama_index IF NOT EXISTS
FOR (d:Desa) ON (d.nama);
```

Ini penting karena:
- **Unique constraint** mencegah duplikat data masuk ke graf
- **Index** membuat query traversal lebih cepat (tidak perlu memindai semua node)

---

## Prompt Engineering

Salah satu aspek yang sering diabaikan: prompt design. Di proyek ini terdapat 3 prompt utama:

### 1. Intent Classification Prompt
LLM diberikan daftar 8 intent + deskripsi + contoh, lalu diminta mengembalikan JSON. Kuncinya: **jelas dan spesifik** — jika intent-nya ambigu, klasifikasi akan sering salah.

### 2. Text-to-Cypher Prompt
LLM diberikan **schema graph** (semua node dan relasi yang ada), instruksi untuk READ, dan beberapa contoh query. Ini penting agar LLM tidak menghasilkan CREATE/DELETE.

### 3. Answer Generator Prompt
Untuk summary_by_province, LLM diminta menganalisis data numerik dan menghasilkan insight dalam Bahasa Indonesia — bukan hanya mengembalikan angka mentah.

---

## Normalisasi & Text Processing

Data Indonesia **sangat tidak terstruktur**. Nama daerah ditulis dengan banyak variasi:

| Asli di CSV | Setelah Normalisasi |
|-------------|---------------------|
| `Kec. Buayan` | `buayan` |
| `KABUPATEN KEBUMEN` | `kebumen` |
| `Kota Bandung` | `bandung` |
| `PROVINSI JAWA TENGAH` | `jawa tengah` |

`normalize.py` menangani semua ini dengan:
1. **Strip prefix** — menghapus "Kec.", "Kab.", "Kota", "Provinsi", dll
2. **Lowercase** — standarisasi casing
3. **Strip whitespace** — hapus spasi berlebih
4. **Hapus tanda baca** — agar pencocokan lebih robust

---

## Error Handling

Sistem memiliki beberapa lapisan pertahanan:

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

Pertahanan berlapis seperti ini penting agar sistem tidak mudah mengalami kegagalan atau mengembalikan data yang salah.

---

## Graph and natural language

Contoh konkret: *"Berapa SPPG di tiap kabupaten di Jawa Tengah?"*

- **Graph**: `MATCH (p:Provinsi {nama:'JAWA TENGAH'})-[:MEMILIKI_KABUPATEN]->(k)-[:MEMILIKI_KECAMATAN]->()-[:MEMILIKI_DESA]->()-[:MEMILIKI_SPPG]->(s) RETURN k.nama, count(s)` 

---

## Performance

Beberapa optimasi yang dilakukan:

- **Batch import** — `UNWIND` untuk bulk insert, bukan satu per satu
- **MERGE bukan CREATE** — deduplication di level database
- **Unique constraints** — mencegah duplikat data masuk
- **Indexes** — pada field yang sering di-query (nama, key)
- **Retry with backoff** — handle transient errors tanpa crash

Dengan optimasi ini, import 27k data selesai dalam hitungan menit, bukan jam.

---

## Saya Tertarik dengan GraphRAG sehingga Mencoba Memahami Ini Terlebih Dahulu

1. **Text-to-Cypher** — implementasi LLM yang generate query Cypher langsung dari natural language, bukan cuma prompt-response
2. **Intent Classification** — custom router yang mengklasifikasikan pertanyaan pengguna ke intent spesifik sebelum query, agar lebih akurat
3. **ETL Pipeline** — transformasi data tabular menjadi graf dengan 5 tipe node dan 10 relasi undirected
---

## Roadmap / Future Work

Beberapa hal yang dapat dikembangkan lebih lanjut:

- [ ] **Vector search** sebagai hybrid — menggabungkan graf traversal DAN vector similarity untuk pertanyaan yang lebih fuzzy
- [ ] **Streaming response** — memberikan respons token-by-token agar pengguna tidak menunggu lama
- [ ] **Multi-turn conversation** — simpan konteks percakapan sebelumnya

---

## Quick Start

```bash
# 1. Setup
git clone https://github.com/<username>/sppg_graphrag.git && cd sppg_graphrag
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Jalankan Ollama
ollama pull qwen2.5:7b

# 3. Import data ke Neo4j (pastikan Neo4j sudah berjalan)
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

---
