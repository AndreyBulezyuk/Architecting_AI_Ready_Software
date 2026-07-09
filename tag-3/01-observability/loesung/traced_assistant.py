"""The one piece Strands' auto-instrumentation does NOT give us for free:
correlating multiple agent turns to one user session in Langfuse.

Everything else — AGENT root span, TOOL span per tool call, GENERATION span per
model turn — comes from Strands itself once tracing.py's StrandsTelemetry is
configured. This module only adds a session-level wrapper span around it.
"""

from typing import Any

from assistant import build_agent
from tracing import tracer

_agent = None  # built lazily so importing this module has no AWS side effect


def ask(question: str, *, session_id: str, tags: list[str] | None = None) -> Any:
    global _agent
    if _agent is None:
        _agent = build_agent()

    with tracer.start_as_current_span("user_turn") as span:
        span.set_attribute("session.id", session_id)
        span.set_attribute("langfuse.trace.tags", tags or ["tag-3/01-exercise"])
        span.set_attribute("gen_ai.prompt", question)
        result = _agent(question)
        span.set_attribute("gen_ai.completion", str(result))
        return result
