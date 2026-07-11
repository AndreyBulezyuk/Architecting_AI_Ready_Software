"""A Strands agent over the travel-report store: the MODEL decides when to use tools.

Run: uv run python assistant.py "Wohin für eine anstrengende Hüttentour?"
"""

import os
import sys

import boto3
from strands import Agent, tool  # pyright: ignore[reportUnknownVariableType]  (decorator ships partial types)
from strands.models import BedrockModel

from config import settings
from store import driver, search

SYSTEM_PROMPT_V1 = """Du bist Reise-Assistent von TravelMate.
Beantworte Fragen zu Reisezielen NUR mit Fakten aus den Tools — nie aus deinem
Weltwissen. Nenne die doc_ids der verwendeten Berichte in der Antwort.
Findet ein Tool nichts Passendes, sage das ehrlich. Antworte knapp, auf Deutsch."""


@tool
def search_travel_reports(question: str) -> str:
    """Semantische Suche in den TravelMate-Reiseberichten.

    Args:
        question: Die Frage oder das Thema, zu dem Berichte gesucht werden.
    """
    hits = search(question, k=3)
    if not hits:
        return "Keine passenden Berichte gefunden."
    return "\n\n".join(f"[{hit.doc_id}#{hit.seq}] {hit.text}" for hit in hits)


@tool
def list_destinations() -> str:
    """Listet alle Reiseziele (doc_ids), zu denen Berichte vorliegen."""
    with driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (c:T4Chunk) RETURN DISTINCT c.doc_id AS doc_id ORDER BY doc_id"
        ).records
    return ", ".join(record["doc_id"] for record in records) or "Keine Berichte vorhanden."


def build_agent() -> Agent:
    profile = os.environ.get("AWS_PROFILE", "default")
    model = BedrockModel(
        boto_session=boto3.Session(profile_name=profile, region_name=settings.aws_region),
        model_id=settings.chat_model_id,
        temperature=0.0,
    )
    return Agent(
        model=model,
        tools=[search_travel_reports, list_destinations],
        system_prompt=SYSTEM_PROMPT_V1,
        callback_handler=None,  # silent: no token streaming to stdout
    )


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Wohin für eine anstrengende Hüttentour?"
    agent = build_agent()
    result = agent(question)
    print(result)
    print("\n--- tools used:", list(result.metrics.tool_metrics))
    print("--- tokens:", result.metrics.accumulated_usage)
