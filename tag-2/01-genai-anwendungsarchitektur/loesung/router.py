"""Model router (part 2): task type -> model tier, every call is metered."""

import time
from dataclasses import dataclass
from typing import Literal

from config import PRICES_PER_MTOK, bedrock_client, settings

TaskType = Literal["classify", "summarize", "draft"]

# the routing table IS the architecture decision — cheap tier unless quality is critical
ROUTES: dict[TaskType, str] = {
    "classify": settings.cheap_model_id,
    "summarize": settings.cheap_model_id,
    "draft": settings.strong_model_id,
}

TASK_PROMPTS: dict[TaskType, str] = {
    "classify": "Ordne den folgenden Text einer Kategorie zu und antworte nur mit ihr:",
    "summarize": "Fasse den folgenden Text in einem Satz zusammen:",
    "draft": "Formuliere eine höfliche, professionelle Antwort-E-Mail auf:",
}


@dataclass
class TaskResult:
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES_PER_MTOK.get(model_id, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def run_task(task_type: TaskType, text: str) -> TaskResult:
    model_id = ROUTES[task_type]
    started = time.perf_counter()
    response = bedrock_client().converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": f"{TASK_PROMPTS[task_type]}\n{text}"}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0},
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    answer = (message.get("content") or [{}])[0].get("text", "")
    usage = response["usage"]
    return TaskResult(
        text=answer,
        model_id=model_id,
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        latency_ms=latency_ms,
        cost_usd=estimate_cost(model_id, usage["inputTokens"], usage["outputTokens"]),
    )


if __name__ == "__main__":
    sample = "Die Buchung war einfach, aber der Transfer zum Hotel kam eine Stunde zu spät."
    for task in ("summarize", "draft"):
        result = run_task(task, sample)
        print(f"[{task} -> {result.model_id}] {result.latency_ms} ms, "
              f"{result.input_tokens}/{result.output_tokens} tok, ~${result.cost_usd:.6f}")
        print(result.text[:200], "\n")
