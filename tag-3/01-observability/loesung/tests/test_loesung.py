"""Live test: the agent's own instrumentation must show up as AGENT + TOOL spans,
correctly correlated to our session id and tags — with zero manual span code
in assistant.py itself.
"""

import time
import uuid
from typing import Any

import botocore.exceptions
import pytest
import store
from config import bedrock_client
from langfuse_api import observations_for_trace, traces_by_tag
from sample_docs import SAMPLE_DOCS
from traced_assistant import ask
from tracing import flush
from strands.agent import AgentResult


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
    for _ in range(10):
        traces = traces_by_tag(tag)
        if traces:
            return traces[0]
        time.sleep(1)
    raise AssertionError(f"no trace with tag {tag!r} appeared within 10s")


def test_agent_run_is_traced_without_manual_spans() -> None:
    tag = f"test-{uuid.uuid4()}"
    session_id = f"sess-{uuid.uuid4()}"

    result: AgentResult = ask(
        "Wohin für eine anstrengende Hüttentour mit Übernachtung?",
        session_id=session_id,
        tags=[tag],
    )
    flush()
    assert "search_travel_reports" in result.metrics.tool_metrics

    trace = _own_trace(tag)
    assert trace["sessionId"] == session_id

    observations = observations_for_trace(str(trace["id"]))
    types = {obs["name"]: obs["type"] for obs in observations}
    # these three names/types come from STRANDS, not from our code —
    # the proof that framework-level instrumentation was enough
    assert types.get("invoke_agent Strands Agents") == "AGENT"
    assert types.get("search_travel_reports") == "TOOL"
    assert "GENERATION" in types.values()
    assert "alpen" in str(result).lower()
