# Demo 05 — Mini-Dokument-Store mit Embedding-Lifecycle

Ablauf (~15 min): Neo4j lokal (`docker compose up -d`) + S3 im eigenen AWS-Account (AWS-Profil aktiv):

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
store.search("welpe", k=3)      # leer! Warum? -> stale, embedding entfernt
store.reembed_stale()
store.search("welpe", k=3)      # jetzt kommt d1
```

**Wichtige Punkte:**

- Schreibpfad und Embedding sind **entkoppelt**: `upsert_document` markiert nur `stale` und **entfernt das `embedding`-Property** — dadurch fliegt der Knoten automatisch aus dem Vector Index (kein Filter nötig). Das Muster von Theorie-Folie 3.
- [embeddings.py](embeddings.py) ist der **einzige Austauschpunkt** für echte Bedrock-Embeddings (Tag 2) — `embedding_model` wird pro Knoten mitgespeichert.
- Rohtext liegt in S3 (Bucket `t05-demo-raw-<account-id>` — Bucket-Namen sind global eindeutig, daher der Suffix), Metadaten + Vektor in Neo4j: **eine** Quelle der Wahrheit, abgeleitete Sichten.
- Der Vector Index arbeitet asynchron: nach Schreib-Bursts `CALL db.awaitIndexes()` — steckt in `reembed_stale()`.
