"""MCP server tests: tool discovery (offline) + live tool calls via in-memory client."""

import asyncio
import inspect

import botocore.exceptions
import pytest
from fastmcp import Client

from config import bedrock_client
from mcp_server import mcp


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


needs_aws = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


# ---------------------------------------------------------------------------
# Offline: tool discovery via in-memory MCP client (no AWS, no Neo4j)
# ---------------------------------------------------------------------------


def test_mcp_server_exposes_exactly_two_tools() -> None:
    async def _list() -> list:
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = asyncio.run(_list())
    names = sorted(t.name for t in tools)
    assert names == ["ask_travelmate", "search_travel_reports"]


def test_tool_schemas_have_correct_parameters() -> None:
    async def _list() -> list:
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = asyncio.run(_list())
    by_name = {t.name: t for t in tools}

    search_params = by_name["search_travel_reports"].inputSchema.get("properties", {})
    assert "query" in search_params
    assert "k" in search_params

    ask_params = by_name["ask_travelmate"].inputSchema.get("properties", {})
    assert "question" in ask_params
    assert "k" not in ask_params  # ask_travelmate hides the k parameter


def test_tool_descriptions_are_non_empty() -> None:
    async def _list() -> list:
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = asyncio.run(_list())
    for tool in tools:
        assert tool.description, f"{tool.name} has empty description"


# ---------------------------------------------------------------------------
# Live: actual tool calls through the MCP protocol (needs AWS + Neo4j)
# ---------------------------------------------------------------------------


@needs_aws
def test_search_tool_returns_results() -> None:
    async def _call() -> str:
        async with Client(mcp) as client:
            result = await client.call_tool("search_travel_reports", {"query": "Strand Kinder"})
            return result.content[0].text

    text = asyncio.run(_call())
    assert "algarve" in text.lower()
    assert "score=" in text


@needs_aws
def test_ask_tool_returns_grounded_answer() -> None:
    async def _call() -> str:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "ask_travelmate", {"question": "Wo kann man mit Kindern baden?"}
            )
            return result.content[0].text

    text = asyncio.run(_call())
    assert "sources=" in text
    assert "model=" in text
    assert "tokens=" in text
