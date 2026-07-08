"""LLM condensation: raw signals -> validated ProfileSummary (contract from chapter 03).

Day-1 approach: prompt for JSON + model_validate_json + one retry. Day 2 (T2/01)
shows the sturdier variant via forced tool call — a deliberate progression.
"""

from pydantic import ValidationError

from config import bedrock_client, settings
from models import ProfileSummary

SYSTEM_PROMPT_V1 = """Du verdichtest Nutzersignale eines Reiseportals zu einem Profil.
Antworte NUR mit einem JSON-Objekt nach diesem Schema, ohne Markdown:
{"interests": ["max 5 einzelne kleingeschriebene woerter, z.B. strand, familie"],
 "persona_summary": "max 2 Saetze",
 "travel_style": "budget|comfort|luxury|unknown"}"""


def _ask(signal_lines: list[str], hint: str | None) -> str:
    prompt = "Signale:\n" + "\n".join(signal_lines)
    if hint:
        prompt += f"\n\nDein letzter Versuch war ungültiges JSON: {hint}"
    response = bedrock_client().converse(
        modelId=settings.bedrock_model_id,
        system=[{"text": SYSTEM_PROMPT_V1}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    return (message.get("content") or [{}])[0].get("text", "")


def _strip_code_fence(raw: str) -> str:
    """LLMs often wraps JSON in a ```json ... ``` fence despite the prompt.
    At temperature 0 this is deterministic, so the retry alone can't recover —
    we peel the fence off before validating."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]  # drop the opening ```json line
        text = text.rstrip().removesuffix("```").rstrip()  # drop the closing fence
    return text


def condense(signal_lines: list[str]) -> ProfileSummary:
    hint: str | None = None
    for _ in range(2):
        raw = _ask(signal_lines, hint)
        try:
            return ProfileSummary.model_validate_json(_strip_code_fence(raw))
        except ValidationError as error:
            hint = str(error)
    raise ValueError(f"model output failed validation twice: {hint}")
