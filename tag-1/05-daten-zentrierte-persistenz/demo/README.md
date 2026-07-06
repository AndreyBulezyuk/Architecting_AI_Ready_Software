# Demo 05 — Mini-Dokument-Store mit Embedding-Lifecycle

Ablauf (~15 min), gegen den lokalen Stack (`docker compose up -d`):

```bash
cd tag-1/05-daten-zentrierte-persistenz/demo
uv sync
uv run pytest -v    # 3 Tests erzählen den kompletten Lifecycle
```

Danach denselben Ablauf einmal von Hand in der `uv run python` REPL:

```python
import store
store.init_schema()
store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier")
store.search("welpe", k=3)      # leer! Warum? -> embedding_stale
store.reembed_stale()
store.search("welpe", k=3)      # jetzt kommt d1
```

**Wichtige Punkte:**

- Schreibpfad und Embedding sind **entkoppelt**: `upsert_document` fasst keine Embeddings an, es markiert nur `embedding_stale` — genau das Muster von Theorie-Folie 3.
- [embeddings.py](embeddings.py) ist der **einzige Austauschpunkt** für echte Bedrock-Embeddings (Tag 2) — `embedding_model` wird pro Zeile mitgespeichert.
- Rohtext liegt in S3, nicht in Postgres: die Quelle der Wahrheit für Re-Embeds und späteres Chunking (Tag 2).
- `to_pgvector` + `::vector`-Cast: pgvector nimmt Literale im `[…]`-Format entgegen.
