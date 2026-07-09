"""Live tests: call the real RAG path, then read the trace back from Langfuse.

Needs both AWS credentials (Bedrock) and the observability profile:
    docker compose --profile observability up -d
"""

import time
import uuid
from typing import Any

import botocore.exceptions
import pytest
import rag
import store
from config import bedrock_client
from langfuse_api import observations_for_trace, traces_by_tag
from sample_docs import SAMPLE_DOCS
from tracing import flush


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    store.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        store.ingest_document(doc_id, text)


def _own_trace(tag: str) -> dict[str, Any]:
    """Poll for the freshly-created trace — the OTLP pipeline is async."""
    for _ in range(10):
        traces = traces_by_tag(tag)
        if traces:
            return traces[0]
        time.sleep(1)
    raise AssertionError(f"no trace with tag {tag!r} appeared within 10s")


def test_answer_produces_a_generation_and_a_retriever_span() -> None:
    unique_tag = f"test-{uuid.uuid4()}"
    original_answer = rag.answer

    def tagged_answer(question: str, k: int = 3, *, request_id: str | None = None) -> rag.RagResult:
        with rag.tracer.start_as_current_span("test-wrapper") as span:
            span.set_attribute("langfuse.trace.tags", [unique_tag])
            return original_answer(question, k, request_id=request_id)

    # the wrapper span carries the unique tag; rag.answer's own span is its child —
    # Langfuse still returns the child GENERATION when we look up observations
    result = tagged_answer("Wo kann man mit Kindern baden?")
    flush()
    assert rag.REFUSAL_MARKER not in result.text

    trace = _own_trace(unique_tag)
    observations = observations_for_trace(str(trace["id"]))
    types = {obs["name"]: obs["type"] for obs in observations}
    assert "rag.answer" in types and types["rag.answer"] == "GENERATION"
    assert "vector_search" in types and types["vector_search"] == "RETRIEVER"

    generation = next(obs for obs in observations if obs["name"] == "rag.answer")
    assert generation["model"] == result.model_id
    assert generation["usageDetails"]["input"] == result.input_tokens
    assert generation["usageDetails"]["output"] == result.output_tokens


def test_request_id_lands_in_trace_metadata() -> None:
    unique_tag = f"test-{uuid.uuid4()}"
    request_id = str(uuid.uuid4())
    with rag.tracer.start_as_current_span("test-wrapper") as span:
        span.set_attribute("langfuse.trace.tags", [unique_tag])
        rag.answer("Wohin für eine Hüttentour?", request_id=request_id)
    flush()

    trace = _own_trace(unique_tag)
    assert trace["metadata"]["request_id"] == request_id
