"""Solution tests: event-driven lifecycle (part 2) and vector-index proof (part 3).

Needs local Neo4j (docker compose up -d) + AWS credentials (S3/SQS) — skipped otherwise.
Queue and bucket stay after the run: uv run python cleanup.py
"""

import botocore.exceptions
import pytest
import store
import worker
from config import s3_client, settings, sqs_client


def _aws_available() -> bool:
    try:
        s3_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def reset() -> str:
    queue_url = store.init_schema()
    with store.driver() as neo4j:
        neo4j.execute_query("MATCH (d:UebDocument) DETACH DELETE d")
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
    for _ in range(8):
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


def test_vector_index_is_online_and_answers_topk() -> None:
    queue_url = reset()
    for i in range(30):
        store.upsert_document(f"doc-{i}", f"Doc {i}", f"wort{i} inhalt beispiel text{i % 7}")
    process_all(queue_url)

    with store.driver() as neo4j:
        records = neo4j.execute_query(
            "SHOW VECTOR INDEXES YIELD name, state, populationPercent "
            "WHERE name = $name RETURN state, populationPercent",
            name=settings.vector_index_name,
        ).records
    assert records, "vector index does not exist"
    assert records[0]["state"] == "ONLINE"
    assert records[0]["populationPercent"] == 100.0

    hits = store.search("beispiel inhalt", k=5)
    assert len(hits) == 5  # the index answers top-k over the 30 embedded documents
