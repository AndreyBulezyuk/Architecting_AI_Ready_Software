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
    result = ask(
        "Wie viele T4Chunk-Knoten gibt es pro doc_id? Nutze die Neo4j-Tools."
    )
    tools_used = list(result.metrics.tool_metrics)
    assert any("cypher" in name or "neo4j" in name for name in tools_used), tools_used
    assert "algarve" in str(result).lower()


def test_agent_combines_own_tool_with_reports() -> None:
    result = ask(
        "Es ist Monat 12: Welche Jahreszeit ist das, und welcher unserer "
        "Berichte passt am ehesten dazu?"
    )
    assert "current_season" in result.metrics.tool_metrics
    assert str(result).strip()
