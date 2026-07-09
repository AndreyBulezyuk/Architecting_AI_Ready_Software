"""RAG answering with a Bedrock guardrail attached to the converse() call.

Two things the guardrail buys us over the bare T2/04 baseline:
  1. off-domain and prompt-injection inputs are refused before/after the model
  2. PII in the output (e.g. an email the model repeats) is anonymized

`stopReason == "guardrail_intervened"` is how converse() signals a block — we map
that to a clear `blocked` flag instead of returning the block text as a normal answer.
"""

from dataclasses import dataclass

from config import bedrock_runtime_client, settings
from store import Hit, search

SYSTEM_PROMPT_V1 = """Du bist Reise-Assistent von TravelMate.
Antworte ausschließlich auf Basis des nummerierten Kontexts, auf Deutsch, knapp.
Wenn der Kontext die Frage nicht beantwortet, sage das ehrlich."""


@dataclass
class GuardedAnswer:
    text: str
    blocked: bool
    sources: list[Hit]


def answer(question: str, guardrail_id: str, k: int = 3) -> GuardedAnswer:
    hits = search(question, k=k)
    context = "\n\n".join(f"[{i + 1}] {hit.text}" for i, hit in enumerate(hits))
    response = bedrock_runtime_client().converse(
        modelId=settings.chat_model_id,
        system=[{"text": SYSTEM_PROMPT_V1}],
        messages=[{
            "role": "user",
            "content": [{"text": f"Kontext:\n{context}\n\nFrage: {question}"}],
        }],
        guardrailConfig={"guardrailIdentifier": guardrail_id, "guardrailVersion": "DRAFT"},
        inferenceConfig={"maxTokens": 400, "temperature": 0},
    )
    blocked = response["stopReason"] == "guardrail_intervened"
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    text = (message.get("content") or [{}])[0].get("text", "")
    return GuardedAnswer(text=text, blocked=blocked, sources=hits)
