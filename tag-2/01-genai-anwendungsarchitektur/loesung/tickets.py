"""SupportTicket contract (part 3): forced tool call + validation + one retry.

The fourth category "kein_anliegen" is the answer to the off-topic test case:
without it the model is FORCED to press unrelated text into a support category.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from config import bedrock_client, settings

TOOL_NAME = "record_support_ticket"


class SupportTicket(BaseModel):
    category: Literal["buchung", "zahlung", "beschwerde", "kein_anliegen", "sonstiges"]
    priority: Literal["niedrig", "normal", "hoch"]
    summary: str = Field(max_length=200)


def _tool_call_input(text: str, hint: str | None) -> dict[str, Any]:
    prompt = (
        "Erfasse die folgende Support-Nachricht als Ticket. Ist es gar kein "
        f"Support-Anliegen, nutze die Kategorie 'kein_anliegen'.\n\nNachricht:\n{text}"
    )
    if hint:
        prompt += f"\n\nHinweis, dein letzter Versuch war ungültig: {hint}"
    response = bedrock_client().converse(
        modelId=settings.cheap_model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [{
                "toolSpec": {
                    "name": TOOL_NAME,
                    "description": "Records the extracted support ticket",
                    "inputSchema": {"json": SupportTicket.model_json_schema()},
                }
            }],
            "toolChoice": {"tool": {"name": TOOL_NAME}},
        },
        inferenceConfig={"maxTokens": 500, "temperature": 0},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    for block in message.get("content") or []:
        tool_use = block.get("toolUse")
        if tool_use and tool_use.get("name") == TOOL_NAME:
            return dict(tool_use.get("input") or {})
    raise RuntimeError("model did not call the required tool")


def extract_ticket(text: str) -> SupportTicket:
    hint: str | None = None
    for _ in range(2):
        raw = _tool_call_input(text, hint)
        try:
            return SupportTicket.model_validate(raw)
        except ValidationError as error:
            hint = str(error)
    raise ValueError(f"model output failed validation twice: {hint}")
