# from ollama import Client
# from app.db import driver

# # PERBAIKAN 1: Hapus '/v1' di belakang URL. 
# # Library Python 'ollama' menggunakan base URL secara langsung.
# # Endpoint '/v1' hanya dipakai jika Anda menggunakan library OpenAI-compatible.
# ollama_client = Client(host='http://localhost:11434')

# def create_vector_index():
#     """
#     Membuat index khusus di Neo4j agar pencarian vector super cepat.
#     nomic-embed-text menghasilkan dimensi 768.
#     """
#     query = """
#     CREATE VECTOR INDEX sppg_embedding_index IF NOT EXISTS
#     FOR (s:SPPG) ON (s.embedding)
#     OPTIONS {
#       indexConfig: {
#         `vector.dimensions`: 768,
#         `vector.similarity_function`: 'cosine'
#       }
#     }
#     """
#     with driver.session() as session:
#         session.run(query)
#     print("Vector index berhasil disiapkan.")


# def create_fulltext_index():
#     """
#     Membuat fulltext index untuk pencarian teks BM25.
#     Berguna untuk hybrid search (gabungan vector + text).
#     """
#     query = """
#     CREATE FULLTEXT INDEX sppg_fulltext IF NOT EXISTS
#     FOR (s:SPPG) ON EACH [s.nama, s.alamat, s.nama_normalized, s.alamat_normalized]
#     """
#     with driver.session() as session:
#         session.run(query)
#     print("Fulltext index berhasil disiapkan.")

# def generate_and_store_embeddings(batch_size: int = 100):
#     # 1. Ambil data SPPG yang BELUM memiliki embedding
#     fetch_query = """
#     MATCH (s:SPPG)
#     WHERE s.embedding IS NULL
#     RETURN s.id AS id, s.nama AS nama, s.alamat AS alamat, 
#            s.desa_normalized AS desa, s.kecamatan_normalized AS kecamatan, 
#            s.kabupaten_normalized AS kabupaten, s.provinsi_normalized AS provinsi
#     """
    
#     with driver.session() as session:
#         result = session.run(fetch_query)
#         records = [record.data() for record in result]
    
#     if not records:
#         print("✅ Semua node SPPG sudah memiliki embedding. Tidak ada yang perlu diproses.")
#         return

#     print(f"⏳ Ditemukan {len(records)} node SPPG untuk di-embed...")
    
#     updates = []
#     for i, record in enumerate(records):
#         # 2. Teks ringkas tapi informatif untuk embedding
#         text_to_embed = (
#             f"{record['nama']}, "
#             f"Desa {record['desa']}, Kec. {record['kecamatan']}, "
#             f"Kab. {record['kabupaten']}, Prov. {record['provinsi']}"
#         )
        
#         # PERBAIKAN 2: Gunakan 'ollama_client' yang sudah dideklarasikan di atas,
#         # BUKAN memanggil 'ollama.embeddings' secara global.
#         try:
#             response = ollama_client.embeddings(model='nomic-embed-text', prompt=text_to_embed)
#             embedding_vector = response['embedding']
#         except Exception as e:
#             print(f"❌ Gagal membuat embedding untuk ID {record['id']}. Error: {e}")
#             continue
        
#         updates.append({
#             'id': record['id'],
#             'embedding': embedding_vector
#         })
        
#         # 4. Simpan ke Neo4j secara bergelombang (Batching)
#         if len(updates) >= batch_size:
#             update_db_batch(updates)
#             print(f"   Terproses {i + 1} / {len(records)} data...")
#             updates = []
            
#     # Simpan sisa data yang belum mencapai ukuran batch
#     if updates:
#         update_db_batch(updates)
#         print(f"   Terproses {len(records)} / {len(records)} data...")

#     print("🎉 Proses generate dan simpan embedding selesai!")

# def update_db_batch(updates: list[dict]):
#     """
#     Menyimpan array embedding ke property 'embedding' pada node SPPG.
#     """
#     update_query = """
#     UNWIND $updates AS update
#     MATCH (s:SPPG {id: update.id})
#     SET s.embedding = update.embedding
#     """
#     with driver.session() as session:
#         session.run(update_query, updates=updates)

# def embed_query(text: str) -> list[float]:
#     """
#     Embed sebuah teks query dan kembalikan vector-nya.
#     Digunakan oleh pipeline pencarian semantik di main.py.
#     Tambahkan konteks agar embedding query lebih kompatibel
#     dengan embedding data di database.
#     """
#     enriched = f"SPPG di Indonesia: {text}"
#     response = ollama_client.embeddings(
#         model='nomic-embed-text',
#         prompt=enriched,
#     )
#     return response['embedding']


# def re_embed_all(batch_size: int = 100):
#     """
#     Re-embed SEMUA node SPPG (reset embedding lama).
#     Berguna setelah mengubah format embedding text.
#     """
#     # Reset semua embedding
#     reset_query = "MATCH (s:SPPG) SET s.embedding = NULL"
#     with driver.session() as session:
#         session.run(reset_query)
#     print("Semua embedding lama di-reset.")

#     # Generate ulang
#     generate_and_store_embeddings(batch_size=batch_size)


# if __name__ == "__main__":
#     create_vector_index()
#     create_fulltext_index()
#     generate_and_store_embeddings(batch_size=250)