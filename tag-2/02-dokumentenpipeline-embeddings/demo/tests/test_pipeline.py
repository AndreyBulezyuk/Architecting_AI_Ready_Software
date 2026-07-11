"""Chunking is tested offline; ingest/search run live against Bedrock + local Neo4j."""

import botocore.exceptions
import pytest
import store
from chunking import chunk_text
from config import bedrock_client
from sample_docs import SAMPLE_DOCS


def test_chunking_respects_size_and_overlap() -> None:
    text = "\n\n".join(f"Absatz {i}: " + "wort " * 40 for i in range(10))
    chunks = chunk_text(text, max_chars=400, overlap_chars=80)
    assert len(chunks) > 1
    assert all(len(chunk) <= 400 for chunk in chunks)
    # overlap: the tail of chunk n reappears at the head of chunk n+1
    assert chunks[0][-40:] in chunks[1]


def test_chunking_rejects_bad_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("text", max_chars=100, overlap_chars=100)


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


needs_aws = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@needs_aws
def test_semantic_search_without_word_overlap() -> None:
    store.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        assert store.ingest_document(doc_id, text) >= 1

    # no shared words with the algarve text — this is what the fake embeddings could not do
    hits = store.search("Urlaub am Wasser mit der ganzen Familie", k=2)
    assert hits[0].doc_id == "algarve"

    hits = store.search("anstrengende Bergwanderung mit Übernachtung", k=2)
    assert hits[0].doc_id == "alpen"
