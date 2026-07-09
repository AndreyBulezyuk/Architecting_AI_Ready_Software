"""Cited RAG answers with honest failure (part 3)."""

from dataclasses import dataclass

from config import bedrock_client, settings
from store import Hit, search

REFUSAL_MARKER = "KEINE_ANTWORT_IM_KONTEXT"

SYSTEM_PROMPT_V1 = f"""Du bist Reise-Assistent von TravelMate.
Antworte ausschließlich auf Basis des nummerierten Kontexts, auf Deutsch, knapp.
Zitiere die verwendeten Kontext-Nummern im Text als [n].
Wenn der Kontext die Frage nicht beantwortet, antworte exakt mit: {REFUSAL_MARKER}"""


@dataclass
class RagAnswer:
    text: str
    sources: list[Hit]

    @property
    def refused(self) -> bool:
        return REFUSAL_MARKER in self.text


def answer(question: str, k: int = 3) -> RagAnswer:
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
    text = (message.get("content") or [{}])[0].get("text", "")
    return RagAnswer(text=text, sources=hits)


if __name__ == "__main__":
    result = answer("Wo kann man mit Kindern baden?")
    print(result.text)
    print("\nQuellen:", [(hit.doc_id, hit.seq) for hit in result.sources])
