# Lösung 02

```bash
# Stack muss laufen (Repo-Root: docker compose --profile emulation up -d)
uv sync
uv run pytest -v
```

Stolpersteine, die in der Übung absichtlich stecken:

- **A:** `create_table` ist asynchron → `get_waiter("table_exists")` vor dem ersten `put_item`; ohne `endpoint_url` läuft boto3 gegen echtes AWS und scheitert an Credentials.
- **B:** Der [Vector Index](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) wird **asynchron** aufgebaut — ohne `CALL db.awaitIndexes()` findet die erste Query manchmal nichts. Abgefragt wird per `db.index.vector.queryNodes(indexName, k, vector)`; der `score` ist eine Ähnlichkeit (größer = ähnlicher), **keine** Distanz.
- **C:** `DETACH DELETE` statt `DELETE`, sonst scheitert das Aufräumen an existierenden Beziehungen.
