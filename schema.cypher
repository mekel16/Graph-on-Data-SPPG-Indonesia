CREATE CONSTRAINT sppg_id_unique IF NOT EXISTS
FOR (s:SPPG)
REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT provinsi_key_unique IF NOT EXISTS
FOR (p:Provinsi)
REQUIRE p.key IS UNIQUE;

CREATE CONSTRAINT kabupaten_key_unique IF NOT EXISTS
FOR (k:KabupatenKota)
REQUIRE k.key IS UNIQUE;

CREATE CONSTRAINT kecamatan_key_unique IF NOT EXISTS
FOR (k:Kecamatan)
REQUIRE k.key IS UNIQUE;

CREATE CONSTRAINT desa_key_unique IF NOT EXISTS
FOR (d:Desa)
REQUIRE d.key IS UNIQUE;

CREATE INDEX sppg_nama_idx IF NOT EXISTS
FOR (s:SPPG)
ON (s.nama_normalized);

CREATE INDEX sppg_alamat_idx IF NOT EXISTS
FOR (s:SPPG)
ON (s.alamat_normalized);

CREATE INDEX provinsi_nama_idx IF NOT EXISTS
FOR (p:Provinsi)
ON (p.nama_normalized);

CREATE INDEX kabupaten_nama_idx IF NOT EXISTS
FOR (k:KabupatenKota)
ON (k.nama_normalized);

CREATE INDEX kecamatan_nama_idx IF NOT EXISTS
FOR (k:Kecamatan)
ON (k.nama_normalized);

CREATE INDEX desa_nama_idx IF NOT EXISTS
FOR (d:Desa)
ON (d.nama_normalized);