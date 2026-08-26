# Penerapan GraphRAG pada Data SPPG Se-Indonesia

_tools_:

<p align="left">
  <img src="https://img.shields.io/badge/Ubuntu-E95420?style=flat&logo=ubuntu&logoColor=white" alt="Ubuntu" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Neo4j-008CC1?style=flat&logo=neo4j&logoColor=white" alt="Neo4j" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white" alt="Ollama" />
</p>

## Inti dari projek ini adalah bahwa bagaimana bisa mendapatkan konteks _natural language_ dari data tabular bukan dengan _vector search_. Tapi dengan pendekatan graf

# From Tabular Data to Graph Intelligence

A visual pipeline that transforms **structured tabular data into a graph representation**, enables **graph-based visualization and reasoning**, and finally converts the resulting insights into **natural language**.

---

## Architecture Overview

<div align="center">

<div style="overflow-x: auto; padding: 20px 0;">

<table>
<tr>
<td align="center" valign="top">

### 01 · Tabular Data

<img src="https://github.com/user-attachments/assets/35bd9f8f-f0ff-4a17-9e32-e3cc7387062f" alt="Tabular Data and Architecture" style="max-width: 900px; width: 100%; height: auto;" />

<p>
Structured data serves as the initial source of information.
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

<img src="https://github.com/user-attachments/assets/40e0eaa8-386b-432f-a472-d20050bd71d2" alt="Graph Visualization" style="max-width: 900px; width: 100%; height: auto;" />

<p>
Tabular relationships are transformed into nodes and edges, producing a graph representation that captures the underlying structure and relationships within the data.
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

<img src="https://github.com/user-attachments/assets/6bf09ca9-6437-4f6f-86a7-bd22eff0bdb7" alt="Natural Language Output" style="max-width: 900px; width: 100%; height: auto;" />

<p>
The graph-derived information is interpreted and transformed into a human-readable natural language response.
</p>

</td>
</tr>
</table>

</div>

</div>

---

## Pipeline

```text
┌─────────────────────┐
│    Tabular Data     │
│                     │
│ Rows · Columns      │
│ Structured Records  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Graph Construction │
│                     │
│ Entities → Nodes    │
│ Relations → Edges    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Graph Reasoning   │
│                     │
│ Structure · Paths   │
│ Relationships       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Natural Language    │
│                     │
│ Graph Insights →    │
│ Human-readable Text │
└─────────────────────┘
```

---

## Core Concept

The system bridges the gap between **structured data** and **human-readable knowledge**.

Instead of treating a table as a collection of independent rows and columns, the pipeline exposes the relationships contained within the data by representing them as a graph.

### 1. Tabular Data

The process begins with structured tabular data containing entities, attributes, and relationships.

```text
Rows + Columns
      │
      ▼
Structured Information
```

### 2. Graph Representation

Relevant entities are represented as **nodes**, while relationships between entities become **edges**.

```text
Entity A ───── relationship ─────> Entity B
   │                                  │
   └──────────── Entity C ────────────┘
```

This representation makes implicit relationships explicit and enables graph-oriented analysis.

### 3. Graph Visualization

The resulting graph provides a visual representation of how entities are connected.

This allows users to inspect:

* Entity relationships
* Connectivity
* Graph structure
* Paths between entities
* Local and global relationships

### 4. Natural Language

The final stage converts graph-derived information into a natural language response.

```text
Graph Structure
      │
      ▼
Relevant Relationships
      │
      ▼
Interpreted Insights
      │
      ▼
Natural Language
```

The result is information that can be consumed directly by humans rather than requiring them to inspect the underlying graph manually.

---

## End-to-End Flow

<div align="center">

**TABULAR DATA**

⬇️

**GRAPH CONSTRUCTION**

⬇️

**GRAPH VISUALIZATION & REASONING**

⬇️

**NATURAL LANGUAGE**

</div>

---

## Why Graphs?

Tabular data is effective for storing structured records, but relationships between records can become difficult to understand when the data grows in complexity.

Graph representation provides a natural abstraction for relational information:

| Data Representation  | Strength                                         |
| -------------------- | ------------------------------------------------ |
| **Tabular**          | Efficient for structured records and attributes  |
| **Graph**            | Explicitly represents entities and relationships |
| **Natural Language** | Makes insights accessible to humans              |

The pipeline therefore combines the strengths of all three representations:

> **Structure → Relationships → Understanding**

---

## Key Idea

The central idea of this project is to create a continuous transformation:

```text
Structured Data
      │
      │  Transform
      ▼
Graph Knowledge
      │
      │  Analyze / Reason
      ▼
Graph Insights
      │
      │  Generate
      ▼
Natural Language
```

This creates a bridge between **data representation, graph intelligence, and human-readable communication**.

---

## Visual Summary

<div align="center">

|         ①        |  →  |     ②     |  →  |           ③          |
| :--------------: | :-: | :-------: | :-: | :------------------: |
| **Tabular Data** |  →  | **Graph** |  →  | **Natural Language** |
|    Structured    |     | Connected |     |    Understandable    |

</div>

---

## Conclusion

This architecture demonstrates how structured tabular information can be progressively transformed into a **graph-based representation** and ultimately expressed as **natural language**.

The goal is not simply to visualize data, but to make the relationships within the data **discoverable, interpretable, and communicable**.

**Tabular Data → Graph → Insights → Natural Language**


