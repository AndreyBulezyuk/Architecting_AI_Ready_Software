# Demo T2/02 — Echte Embeddings auf dem bekannten Store

Ablauf (~15 min), lokales Neo4j + echtes Bedrock (Embeddings kosten Bruchteile eines Cents):

```bash
cd tag-2/02-dokumentenpipeline-embeddings/demo
uv sync
uv run pytest -v     # Chunking offline, Ingest+Suche live
```

Danach den Kontrast zu Tag 1 live zeigen (REPL):

```python
import store
from sample_docs import SAMPLE_DOCS
store.init_schema()
for doc_id, text in SAMPLE_DOCS.items():
    store.ingest_document(doc_id, text)

store.search("Urlaub am Wasser mit der ganzen Familie", k=2)
# → Algarve-Bericht auf Platz 1 — OHNE ein einziges gemeinsames Wort.
# Die Fake-Embeddings aus tag-1/05 hätten hier zufällig geraten.
```

**Wichtige Punkte:**

- [embeddings.py](embeddings.py) ist der versprochene **einzige Austauschpunkt** aus Kapitel 05: Fake-Hash raus, `cohere.embed-multilingual-v3` rein — Store und Lifecycle unverändert.
- `input_type` beachten: `search_document` beim Ingest, `search_query` bei der Suche (Folie 4).
- Embeddings laufen über `invoke_model` mit Provider-JSON — `converse` ist nur für Chat-Modelle.
- [chunking.py](chunking.py) ist eine pure Funktion und offline testbar — die Parameter (`600/100`) sind Startwerte, kein Naturgesetz: messen kommt in der Übung.
