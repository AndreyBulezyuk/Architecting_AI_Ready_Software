"""Structured output via forced tool use (theorie.md, slide 5).

The model MUST call the tool (toolChoice), the tool schema comes straight from the
Pydantic model, and validation still runs on our side — one retry on failure.

Run: uv run python structured.py "Max, 34, aus Berlin, reist gern mit Familie ans Meer."
"""

import sys
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from config import bedrock_client, settings

TOOL_NAME = "record_traveler_profile"


class TravelerProfile(BaseModel):
    name: str
    age: int | None = None
    home_city: str | None = None
    interests: list[str] = Field(default_factory=list, max_length=5)


def _tool_call_input(text: str, hint: str | None) -> dict[str, Any]:
    """One converse call with a forced tool call; returns the raw toolUse input."""
    prompt = f"Extrahiere das Reiseprofil aus diesem Text:\n{text}"
    if hint:
        prompt += f"\n\nHinweis, dein letzter Versuch war ungültig: {hint}"
    response = bedrock_client().converse(
        modelId=settings.bedrock_model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [{
                "toolSpec": {
                    "name": TOOL_NAME,
                    "description": "Records the extracted traveler profile",
                    "inputSchema": {"json": TravelerProfile.model_json_schema()},
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


def extract_profile(text: str) -> TravelerProfile:
    """Forced tool call + Pydantic validation, one retry with the error as hint."""
    hint: str | None = None
    for _ in range(2):
        raw = _tool_call_input(text, hint)
        try:
            return TravelerProfile.model_validate(raw)
        except ValidationError as error:
            hint = str(error)
    raise ValueError(f"model output failed validation twice: {hint}")


if __name__ == "__main__":
    sample = sys.argv[1] if len(sys.argv) > 1 else (
        "Max, 34, aus Berlin, reist gern mit seiner Familie ans Meer und wandert."
    )
    print(extract_profile(sample).model_dump_json(indent=2))
