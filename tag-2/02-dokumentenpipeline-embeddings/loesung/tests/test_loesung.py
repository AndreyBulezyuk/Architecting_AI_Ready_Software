"""Live tests: chunking experiment via hit rate + cited RAG answers with refusal."""

import botocore.exceptions
import pytest
import store
from config import bedrock_client
from evaluation import QUESTIONS, hit_rate_at_k
from rag import answer
from sample_docs import SAMPLE_DOCS


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")

GOOD_LABEL = "UebChunk"  # 600 chars / 100 overlap (defaults)
TINY_LABEL = "UebChunkTiny"  # 150 chars / 0 overlap


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    for label, max_chars, overlap in ((GOOD_LABEL, 600, 100), (TINY_LABEL, 150, 0)):
        store.init_schema(label)
        for doc_id, text in SAMPLE_DOCS.items():
            store.ingest_document(
                doc_id, text, label=label, max_chars=max_chars, overlap_chars=overlap
            )


def test_hit_rate_with_default_chunking_is_high() -> None:
    result = hit_rate_at_k(QUESTIONS, k=3, label=GOOD_LABEL)
    assert result.hit_rate >= 0.8, f"only {result.hits}/{result.total} questions hit"


def test_tiny_chunks_are_not_better() -> None:
    good = hit_rate_at_k(QUESTIONS, k=3, label=GOOD_LABEL)
    tiny = hit_rate_at_k(QUESTIONS, k=3, label=TINY_LABEL)
    assert good.hit_rate >= tiny.hit_rate


def test_answer_cites_sources() -> None:
    result = answer("Wo kann man mit Kindern baden?")
    assert not result.refused
    assert "[1]" in result.text or "[2]" in result.text or "[3]" in result.text
    assert any(hit.doc_id == "algarve" for hit in result.sources)


def test_off_topic_question_is_refused() -> None:
    result = answer("Welche Programmiersprache ist die beste?")
    assert result.refused
