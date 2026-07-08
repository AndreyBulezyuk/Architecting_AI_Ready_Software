"""Lifecycle tests: local Neo4j + real AWS S3 (skipped without credentials)."""

import botocore.exceptions
import pytest
import store
from config import s3_client


def _aws_available() -> bool:
    try:
        s3_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def reset() -> None:
    store.init_schema()
    with store.driver() as neo4j:
        neo4j.execute_query("MATCH (d:Document) DETACH DELETE d")


def seed() -> None:
    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier")
    store.upsert_document("d2", "Autopflege", "auto motor reifen politur wagen")
    store.upsert_document("d3", "Katzenfutter", "katze futter napf tier")


def stale_count() -> int:
    with store.driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (d:Document) WHERE d.stale RETURN count(d) AS n"
        ).records
    return int(records[0]["n"])


def test_ingest_marks_stale_and_reembed_clears_it() -> None:
    reset()
    seed()
    assert stale_count() == 3
    assert store.reembed_stale() == 3
    assert stale_count() == 0


def test_search_finds_semantically_closest_document() -> None:
    reset()
    seed()
    store.reembed_stale()
    results = store.search("welpe hund tier", k=2)
    assert results[0] == ("d1", "Hundeerziehung")


def test_updated_document_disappears_until_reembedded() -> None:
    reset()
    seed()
    store.reembed_stale()
    # source changes -> derived view is stale -> no embedding -> out of the index
    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier geduld")
    hits = [doc_id for doc_id, _ in store.search("welpe hund tier", k=3)]
    assert "d1" not in hits
    store.reembed_stale()
    hits = [doc_id for doc_id, _ in store.search("welpe hund tier", k=3)]
    assert hits[0] == "d1"
