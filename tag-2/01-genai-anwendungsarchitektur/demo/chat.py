"""Basic converse call with usage tracking (theorie.md, slides 4+6).

Run: uv run python chat.py "Was ist ein Event-Bus?"
"""

import sys
from dataclasses import dataclass

from config import bedrock_client, settings

SYSTEM_PROMPT_V1 = """Du bist Reise-Assistent von TravelMate.
Antworte auf Deutsch, maximal drei Sätze."""


@dataclass
class ChatResult:
    text: str
    input_tokens: int
    output_tokens: int


def ask(question: str, *, system: str = SYSTEM_PROMPT_V1, max_tokens: int = 300) -> ChatResult:
    response = bedrock_client().converse(
        modelId=settings.bedrock_model_id,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": question}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    text = (message.get("content") or [{}])[0].get("text", "")
    usage = response["usage"]
    return ChatResult(text, usage["inputTokens"], usage["outputTokens"])


if __name__ == "__main__":
    result = ask(sys.argv[1] if len(sys.argv) > 1 else "Was ist ein Event-Bus?")
    print(result.text)
    print(f"\n--- tokens: in={result.input_tokens} out={result.output_tokens}")
