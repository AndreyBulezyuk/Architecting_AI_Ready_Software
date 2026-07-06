# Lösung 02

```bash
# Stack muss laufen (Repo-Root: docker compose up -d)
uv sync
uv run pytest -v
```

Stolpersteine, die in der Übung absichtlich stecken:

- **A:** `create_table` ist asynchron → `get_waiter("table_exists")` vor dem ersten `put_item`; ohne `endpoint_url` läuft boto3 gegen echtes AWS und scheitert an Credentials.
- **B:** `<=>` ist Cosine Distance, `<->` L2, `<#>` negatives Inner Product ([pgvector-README](https://github.com/pgvector/pgvector#querying)) — Distanz: kleiner = ähnlicher, daher `ORDER BY … ASC` (Default).
- **C:** `DETACH DELETE` statt `DELETE`, sonst scheitert das Aufräumen an existierenden Beziehungen.
