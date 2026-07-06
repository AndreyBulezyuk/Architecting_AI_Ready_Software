"""Solution tests: event-driven lifecycle (part 2) and EXPLAIN index proof (part 3)."""

import psycopg
import store
import worker
from config import settings, sqs_client
from embeddings import embed, to_pgvector
from psycopg import sql

TABLE = sql.Identifier(settings.table_name)


def reset() -> str:
    queue_url = store.init_schema()
    with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("DELETE FROM {table}").format(table=TABLE))
    sqs = sqs_client()
    while messages := sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get(
        "Messages"
    ):
        for message in messages:
            receipt_handle = message.get("ReceiptHandle")
            assert receipt_handle is not None
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    return queue_url


def process_all(queue_url: str) -> None:
    for _ in range(5):
        if worker.poll_once(queue_url) == 0:
            return


def test_event_driven_reembed_lifecycle() -> None:
    queue_url = reset()

    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier")
    assert store.search("welpe hund", k=3) == []  # stale until the event is processed

    process_all(queue_url)
    assert store.search("welpe hund", k=3)[0][0] == "d1"

    # update -> stale again -> event processing brings it back
    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier geduld")
    assert all(doc_id != "d1" for doc_id, _ in store.search("welpe hund", k=3))
    process_all(queue_url)
    assert store.search("welpe hund", k=3)[0][0] == "d1"


def test_explain_uses_hnsw_index_when_seqscan_disabled() -> None:
    queue_url = reset()
    for i in range(200):
        store.upsert_document(f"doc-{i}", f"Doc {i}", f"wort{i} inhalt beispiel text{i % 7}")
    process_all(queue_url)

    with psycopg.connect(settings.postgres_dsn) as conn:
        # small tables legitimately favour a Seq Scan — disable it to prove the index works
        conn.execute("SET enable_seqscan = off")
        plan_rows = conn.execute(
            sql.SQL(
                "EXPLAIN SELECT id FROM {table} ORDER BY embedding <=> %s::vector LIMIT 5"
            ).format(table=TABLE),
            (to_pgvector(embed("beispiel inhalt")),),
        ).fetchall()
    plan = "\n".join(row[0] for row in plan_rows)
    assert f"Index Scan using {settings.table_name}_embedding_hnsw" in plan
