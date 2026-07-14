"""Live tests: own tool + MCP database access (the agent writes its own Cypher).

The first MCP run downloads mcp-neo4j-cypher via uvx — allow ~1 min.
"""

import botocore.exceptions
import pytest
import store
from config import bedrock_client
from mcp_agent import ask
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


def test_agent_queries_the_database_via_mcp() -> None:
    # Seed exactly 345 bare 'T2C5Chunk' nodes; the agent has to count them via Cypher.
    store.delete_all_nodes("T2C5Chunk")
    store.create_nodes("T2C5Chunk", 345)
    try:
        result = ask("Zähle 'T2C5Chunk' Knoten. Nutze die Neo4j-Tools.")
        tools_used = list(result.metrics.tool_metrics)
        print(result)
        assert any("cypher" in name or "neo4j" in name for name in tools_used), tools_used
        assert "345" in str(result), result
    finally:
        # Clean up: leftover property-less nodes would pollute the schema that
        # get_neo4j_schema reports in later runs (agent then misreads the graph).
        store.delete_all_nodes("T2C5Chunk")


def test_agent_combines_own_tool_with_reports() -> None:
    result = ask(
        "Es ist Monat 12: Welche Jahreszeit ist das, und welcher unserer "
        "Berichte passt am ehesten dazu?"
    )
    assert "current_season" in result.metrics.tool_metrics
    assert str(result).strip()
