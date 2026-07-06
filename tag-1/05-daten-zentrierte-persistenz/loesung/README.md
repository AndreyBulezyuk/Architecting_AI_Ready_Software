# Lösung 05

```bash
uv sync
uv run pytest -v    # gegen den lokalen Stack (docker compose up -d)
```

Stolpersteine aus der Übung:

- **Verlorene Updates** (Teil 2, Recherchefrage): `reembed_document` merkt sich `updated_at` beim Lesen und setzt `embedding_stale` nur zurück, `WHERE updated_at = <gelesener Wert>` — ein zwischenzeitliches Update bleibt stale und wird vom nächsten Event eingesammelt.
- **EXPLAIN zeigt Seq Scan** (Teil 3): Bei 200 Zeilen ist das die **richtige** Planner-Entscheidung. `SET enable_seqscan = off` zwingt den `Index Scan using documents_ueb_embedding_hnsw` — im Test genau so bewiesen. In Produktion nie global abschalten; das Setting ist ein Diagnose-Werkzeug.
- **Direkte SQS-Queue statt Bus** (Abschlussfrage 1): reicht, solange es genau einen Consumer-Typ gibt und niemand filtern muss. Sobald ein zweiter Interessent auftaucht → EventBridge-Rule davor (Kapitel 04).
- `embedding_model` pro Zeile (Abschlussfrage 3): Beim Modellwechsel lassen sich alte und neue Embeddings unterscheiden und **gemischt** betreiben — Migration in Batches statt Big Bang.
