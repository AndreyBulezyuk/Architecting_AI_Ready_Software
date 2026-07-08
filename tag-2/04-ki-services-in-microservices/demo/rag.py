"""RAG core wrapped for service use: every call returns data AND operational metrics.

The service layer (service.py) never talks to Bedrock or Neo4j directly — this
module is the seam where GraphRAG (T2/03) could replace the baseline unchanged.
"""

import time
from dataclasses import dataclass

from config import bedrock_client, settings
from store import Hit, search

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


def answer(question: str, k: int = 3) -> RagResult:
    started = time.perf_counter()
    hits = search(question, k=k)
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
    return RagResult(
        text=(message.get("content") or [{}])[0].get("text", ""),
        sources=hits,
        model_id=settings.chat_model_id,
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
