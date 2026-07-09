"""Wires Strands' built-in OTel export to Langfuse, plus one tracer of our own
for session-level correlation across agent turns (see ask() in traced_assistant.py).

Verified: Strands emits a full trace on its own — AGENT root span, one TOOL span
per tool call, one GENERATION span per model turn, all correctly classified by
Langfuse without a single manual span in assistant.py.
"""

import base64

from opentelemetry import trace
from opentelemetry.trace import Tracer
from pydantic_settings import BaseSettings
from strands.telemetry import StrandsTelemetry


class LangfuseSettings(BaseSettings):
    host: str = "http://localhost:3000"
    public_key: str = "pk-lf-training-0000000000000000"
    secret_key: str = "sk-lf-training-0000000000000000"
    service_name: str = "travel-agent"


def build_tracer(settings: LangfuseSettings | None = None) -> Tracer:
    settings = settings or LangfuseSettings()
    auth = base64.b64encode(f"{settings.public_key}:{settings.secret_key}".encode()).decode()

    # StrandsTelemetry owns the global TracerProvider — everything the SDK emits
    # (agent/tool/model spans) goes through it automatically, no code changes
    # needed in assistant.py.
    StrandsTelemetry().setup_otlp_exporter(
        endpoint=f"{settings.host}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {auth}"},
    )
    # our own tracer shares that same provider (trace.get_tracer reads the
    # global one) — spans we open here and Strands' spans end up in one trace
    return trace.get_tracer(settings.service_name)


def flush() -> None:
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if force_flush is not None:
        force_flush()


tracer = build_tracer()
