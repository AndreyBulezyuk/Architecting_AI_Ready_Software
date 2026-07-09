"""RAG core, now traced: one root span per answer() call, one child span per
retrieval step. Attribute names follow the OTel GenAI Semantic Conventions,
verified against a live Langfuse instance (see theorie.md for the full table).
"""

import time
from dataclasses import dataclass

from config import bedrock_client, settings
from store import Hit, search
from tracing import tracer

REFUSAL_MARKER = "KEINE_ANTWORT_IM_KONTEXT"

SYSTEM_PROMPT_V1 = f"""Du bist Reise-Assistent von TravelMate.
Antworte ausschließlich auf Basis des nummerierten Kontexts, auf Deutsch, knapp.
Zitiere die verwendeten Kontext-Nummern im Text als [n].
Wenn der Kontext die Frage nicht beantwortet, antworte exakt mit: {REFUSAL_MARKER}"""


@dataclass
class RagResult:
    text: str
    sources: list[Hit]
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _retrieve(question: str, k: int) -> list[Hit]:
    # langfuse.observation.type=retriever is how Langfuse tells retrieval steps
    # apart from LLM generations in the trace tree — verified via the OTLP API
    with tracer.start_as_current_span("vector_search") as span:
        span.set_attribute("langfuse.observation.type", "retriever")
        span.set_attribute("langfuse.observation.input", question)
        hits = search(question, k=k)
        span.set_attribute(
            "langfuse.observation.output", ", ".join(f"{h.doc_id}#{h.seq}" for h in hits)
        )
        return hits


def answer(question: str, k: int = 3, *, request_id: str | None = None) -> RagResult:
    started = time.perf_counter()
    with tracer.start_as_current_span("rag.answer") as span:
        if request_id:
            span.set_attribute("langfuse.trace.metadata.request_id", request_id)
        span.set_attribute("langfuse.trace.tags", ["tag-3/01", "rag-baseline"])
        span.set_attribute("gen_ai.prompt", question)

        hits = _retrieve(question, k)
        context = "\n\n".join(f"[{i + 1}] {hit.text}" for i, hit in enumerate(hits))
        response = bedrock_client().converse(
            modelId=settings.chat_model_id,
            system=[{"text": SYSTEM_PROMPT_V1}],
            messages=[{
                "role": "user",
                "content": [{"text": f"Kontext:\n{context}\n\nFrage: {question}"}],
            }],
            inferenceConfig={"maxTokens": 400, "temperature": 0},
        )
        message = response["output"].get("message")
        assert message is not None, "model returned no message"
        usage = response["usage"]
        text = (message.get("content") or [{}])[0].get("text", "")

        # presence of gen_ai.request.model is what makes Langfuse classify this
        # span as a GENERATION (verified) — no separate "mark as LLM call" flag
        span.set_attribute("gen_ai.system", "aws.bedrock")
        span.set_attribute("gen_ai.request.model", settings.chat_model_id)
        span.set_attribute("gen_ai.usage.input_tokens", usage["inputTokens"])
        span.set_attribute("gen_ai.usage.output_tokens", usage["outputTokens"])
        span.set_attribute("gen_ai.completion", text)

        return RagResult(
            text=text,
            sources=hits,
            model_id=settings.chat_model_id,
            input_tokens=usage["inputTokens"],
            output_tokens=usage["outputTokens"],
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
