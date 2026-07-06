"""Lifecycle tests against the local stack (postgres + LocalStack S3)."""

import psycopg
import store
from config import settings


def reset() -> None:
    store.init_schema()
    with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
        conn.execute("DELETE FROM documents")


def seed() -> None:
    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier")
    store.upsert_document("d2", "Autopflege", "auto motor reifen politur wagen")
    store.upsert_document("d3", "Katzenfutter", "katze futter napf tier")


def test_ingest_marks_stale_and_reembed_clears_it() -> None:
    reset()
    seed()
    with psycopg.connect(settings.postgres_dsn) as conn:
        stale = conn.execute("SELECT count(*) FROM documents WHERE embedding_stale").fetchone()
        assert stale is not None and stale[0] == 3
    assert store.reembed_stale() == 3
    with psycopg.connect(settings.postgres_dsn) as conn:
        stale = conn.execute("SELECT count(*) FROM documents WHERE embedding_stale").fetchone()
        assert stale is not None and stale[0] == 0


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
    # source changes -> derived view is stale -> excluded from search
    store.upsert_document("d1", "Hundeerziehung", "hund welpe leine training tier geduld")
    hits = [doc_id for doc_id, _ in store.search("welpe hund tier", k=3)]
    assert "d1" not in hits
    store.reembed_stale()
    hits = [doc_id for doc_id, _ in store.search("welpe hund tier", k=3)]
    assert hits[0] == "d1"
