"""OTel tracer wired to the local Langfuse OTLP endpoint.

Verified against a live Langfuse instance (docker compose --profile observability):
Langfuse's OTel ingest is at /api/public/otel and auto-classifies spans by their
attributes — see theorie.md for the full, tested attribute table.
"""

import base64

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer
from pydantic_settings import BaseSettings


class LangfuseSettings(BaseSettings):
    host: str = "http://localhost:3000"
    # headless-init defaults from the root docker-compose.yml (training only)
    public_key: str = "pk-lf-training-0000000000000000"
    secret_key: str = "sk-lf-training-0000000000000000"
    service_name: str = "assistant-service"


def build_tracer(settings: LangfuseSettings | None = None) -> Tracer:
    settings = settings or LangfuseSettings()
    auth = base64.b64encode(
        f"{settings.public_key}:{settings.secret_key}".encode()
    ).decode()

    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: settings.service_name})
    )
    exporter = OTLPSpanExporter(
        endpoint=f"{settings.host}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {auth}"},
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(settings.service_name)


def flush() -> None:
    """Force-export buffered spans — call before the process exits (tests, scripts)."""
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if force_flush is not None:
        force_flush()


# module-level tracer: every instrumented function imports this one instance
tracer = build_tracer()
