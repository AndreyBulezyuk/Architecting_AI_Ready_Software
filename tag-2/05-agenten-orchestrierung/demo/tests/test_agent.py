"""Live agent tests: the model must actually USE the tools (metrics prove it)."""

import botocore.exceptions
import pytest
import store
from assistant import build_agent
from config import bedrock_client
from sample_docs import SAMPLE_DOCS


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


def test_agent_answers_via_search_tool() -> None:
    agent = build_agent()
    result = agent("Wohin für eine anstrengende Hüttentour mit Übernachtung?")
    text = str(result)
    assert text.strip()
    # the proof that this is an agent, not a chat: the tool was actually called
    assert "search_travel_reports" in result.metrics.tool_metrics
    assert "alpen" in text.lower()


def test_agent_picks_the_listing_tool_for_inventory_questions() -> None:
    agent = build_agent()
    result = agent("Zu welchen Reisezielen habt ihr überhaupt Berichte?")
    assert "list_destinations" in result.metrics.tool_metrics
    assert "algarve" in str(result).lower()
