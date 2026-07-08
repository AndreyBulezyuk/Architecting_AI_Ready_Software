# Lösung 05

```bash
uv sync
uv run pytest -v           # Neo4j lokal (docker compose up -d) + S3/SQS im AWS-Account
uv run python cleanup.py   # Queue + Bucket danach entfernen (Wegwerf-Design)
```

Stolpersteine aus der Übung:

- **Verlorene Updates** (Teil 2, Recherchefrage): `reembed_document` kann sich `updated_at` beim Lesen merken und `stale` nur zurücksetzen, wenn es unverändert ist — ein zwischenzeitliches Update bleibt dann stale und wird vom nächsten Event eingesammelt. (Die Referenzlösung ignoriert das bewusst: das nächste Event repariert den Zustand — dokumentierte Entscheidung.)
- **Index-Beweis** (Teil 3): `SHOW VECTOR INDEXES` zeigt `state: ONLINE` und `populationPercent: 100.0` — direkt nach einem Schreib-Burst kann die Population noch laufen, daher `CALL db.awaitIndexes()` im Store. Der `score` von `queryNodes` ist eine **Ähnlichkeit** (größer = besser), keine Distanz — Sortierung `DESC`.
- **Eigenes Label** (`UebDocument`): pro Label+Property ist nur ein Vector Index erlaubt — die Demo belegt `Document` bereits.
- **Direkte SQS-Queue statt Bus** (Abschlussfrage 1): reicht, solange es genau einen Consumer-Typ gibt und niemand filtern muss. Sobald ein zweiter Interessent auftaucht → EventBridge-Rule davor (Kapitel 04).
- `embedding_model` pro Knoten (Abschlussfrage 3): Beim Modellwechsel lassen sich alte und neue Embeddings unterscheiden und **gemischt** betreiben — Migration in Batches statt Big Bang. Ändert sich die **Dimension**, braucht es zusätzlich einen neuen Index (fix pro Index!).
