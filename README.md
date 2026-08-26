# Penerapan GraphRAG pada Data SPPG Se-Indonesia

_tools_:

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



