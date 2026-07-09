"""Model tiering: the same task on Haiku vs. Sonnet, with measured token cost.

The point is not "Sonnet is better" but "know what the quality actually costs" —
for a classification/summarization task the cheap tier is often indistinguishable,
and the price gap is several times over.

Run: uv run python tiering.py
"""

from dataclasses import dataclass

from config import bedrock_client, settings
from cost import TokenCounts, cost_of


@dataclass
class TierResult:
    model_id: str
    text: str
    cost_usd: float


def _run(model_id: str, task: str) -> TierResult:
    response = bedrock_client().converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": task}]}],
        inferenceConfig={"maxTokens": 120, "temperature": 0},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    text = (message.get("content") or [{}])[0].get("text", "")
    usage = response["usage"]
    tokens = TokenCounts(
        input_tokens=usage["inputTokens"], output_tokens=usage["outputTokens"]
    )
    return TierResult(model_id, text, cost_of(model_id, tokens).total)


def compare_tiers(task: str) -> tuple[TierResult, TierResult]:
    return _run(settings.cheap_model_id, task), _run(settings.strong_model_id, task)


if __name__ == "__main__":
    task = (
        "Klassifiziere diese Support-Nachricht in genau ein Wort "
        "(buchung/zahlung/beschwerde): 'Meine Kreditkarte wurde doppelt belastet.'"
    )
    cheap, strong = compare_tiers(task)
    print(f"Haiku:  {cheap.text.strip()!r}  ${cheap.cost_usd:.6f}")
    print(f"Sonnet: {strong.text.strip()!r}  ${strong.cost_usd:.6f}")
    if cheap.cost_usd:
        print(f"\nSonnet kostet das {strong.cost_usd / cheap.cost_usd:.1f}-fache für dieselbe Klassifikation")
