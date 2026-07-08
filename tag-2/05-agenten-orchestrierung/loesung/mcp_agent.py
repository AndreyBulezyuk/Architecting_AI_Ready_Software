"""Exercise solution: the agent gets database access via MCP (official Neo4j server).

The MCP server (mcp-neo4j-cypher) runs as a subprocess via uvx and exposes tools
like get_neo4j_schema / read_neo4j_cypher — the agent writes its own Cypher.

Run: uv run python mcp_agent.py "Wie viele Chunks gibt es pro Reiseziel?"
"""

import os
import sys
from typing import Any

import boto3
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool  # pyright: ignore[reportUnknownVariableType]  (decorator ships partial types)
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from assistant import search_travel_reports
from config import settings

SYSTEM_PROMPT_V2 = """Du bist Reise-Assistent von TravelMate mit Datenbank-Zugriff.
Für inhaltliche Fragen zu Reisezielen nutze search_travel_reports.
Für Struktur- und Zahlenfragen (wie viele, welche Knoten, Statistik) nutze die
Neo4j-Tools: erst das Schema holen, dann NUR lesende Cypher-Queries ausführen.
Antworte knapp, auf Deutsch. Erfinde nichts, was die Tools nicht liefern."""

SEASONS = {12: "winter", 1: "winter", 2: "winter", 3: "frühling", 4: "frühling",
           5: "frühling", 6: "sommer", 7: "sommer", 8: "sommer",
           9: "herbst", 10: "herbst", 11: "herbst"}


@tool
def current_season(month: int) -> str:
    """Liefert die Jahreszeit zu einem Monat (1-12).

    Args:
        month: Monat als Zahl von 1 bis 12.
    """
    return SEASONS.get(month, "unbekannt")


def neo4j_mcp_client() -> MCPClient:
    """Official Neo4j MCP server as a uvx subprocess (read access for the agent)."""
    return MCPClient(lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=["mcp-neo4j-cypher"],
        env={
            "NEO4J_URI": settings.neo4j_uri,
            "NEO4J_USERNAME": settings.neo4j_user,
            "NEO4J_PASSWORD": settings.neo4j_password,
            "PATH": os.environ.get("PATH", ""),
        },
    )))


def ask(question: str) -> Any:
    """Build the agent inside the MCP session and answer one question."""
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    model = BedrockModel(
        boto_session=boto3.Session(profile_name=profile, region_name=settings.aws_region),
        model_id=settings.chat_model_id,
        temperature=0.0,
    )
    mcp_client = neo4j_mcp_client()
    with mcp_client:  # MCP tools are only usable while the session is open
        mcp_tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=model,
            tools=[search_travel_reports, current_season, *mcp_tools],
            system_prompt=SYSTEM_PROMPT_V2,
            callback_handler=None,
        )
        return agent(question)


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Wie viele Chunks gibt es pro Reiseziel?"
    result = ask(question)
    print(result)
    print("\n--- tools used:", list(result.metrics.tool_metrics))
