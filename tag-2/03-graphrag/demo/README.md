# Demo T2/03 — GraphRAG von Hand

Ablauf (~15 min): Neo4j läuft, AWS-Profil aktiv. Ingest kostet ~5 Extraktions-Calls (Centbereich).

```bash
cd tag-2/03-graphrag/demo
uv sync
uv run pytest -v          # Ingest (5 Docs) + Graph-Beweise + kombinierte Antwort
uv run python graphrag.py # die Demo-Frage mit Kontext-Herkunft auf der Konsole
```

Danach im [Neo4j Browser](http://localhost:7474) den Graphen zeigen:

```cypher
MATCH (d:T3Doc)-[:MENTIONS]->(e:T3Entity) RETURN d, e;          // das Entity-Netz
MATCH (a:T3Doc)-[:MENTIONS]->(e)<-[:MENTIONS]-(b:T3Doc)
WHERE a.doc_id < b.doc_id RETURN a.doc_id, e.name, b.doc_id;    // wer teilt was?
```

**Wichtige Punkte:**

- [kg.py](kg.py): Die Extraktion ist der **T2/01-Vertrag** (erzwungener Tool-Call + Pydantic + Retry) — bewusst kein "antworte mit JSON"-Prompt (Code-Fence-Falle). `MERGE` macht "wandern" aus zwei Docs zu **einem** Knoten.
- [graphrag.py](graphrag.py): Der Unterschied zur T2/02-Baseline ist **eine** zusätzliche Cypher-Query (`graph_expansion`) — kein zweiter LLM-Call, kein Rewrite.
- Die `via`-Angabe pro Kontext-Chunk (`vector` vs. `graph:wandern`) macht erklärbar, **warum** ein Dokument im Kontext gelandet ist.
- Live zeigen: `uv run python graphrag.py` — die Frage "wandern und danach im Meer baden" zieht den Madeira-Bericht über die Graph-Kante, obwohl die Vektor-Treffer woanders lagen.
