"""Standalone guardrail check via apply_guardrail — guards text that does NOT go
through converse(), e.g. a retrieved document before it enters the prompt.

This is the RAG-specific defence: indirect prompt injection hides instructions in
the *knowledge base*, not the user's question. converse()'s guardrail only sees
the final prompt; apply_guardrail lets us screen each source chunk on its own.
"""

from dataclasses import dataclass
from typing import Literal

from config import bedrock_runtime_client


@dataclass
class ScanResult:
    intervened: bool
    triggered_topics: list[str]
    text: str  # possibly anonymized


def scan(text: str, guardrail_id: str, source: Literal["INPUT", "OUTPUT"]) -> ScanResult:
    response = bedrock_runtime_client().apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion="DRAFT",
        source=source,
        content=[{"text": {"text": text}}],
    )
    topics: list[str] = []
    for assessment in response.get("assessments", []):
        for topic in assessment.get("topicPolicy", {}).get("topics", []):
            name = topic.get("name")
            if name:
                topics.append(name)
    outputs = response.get("outputs", [])
    scrubbed = outputs[0].get("text", text) if outputs else text
    return ScanResult(
        intervened=response.get("action") == "GUARDRAIL_INTERVENED",
        triggered_topics=topics,
        text=scrubbed,
    )
