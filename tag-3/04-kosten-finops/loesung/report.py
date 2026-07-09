"""Cost report over a mixed workload: each task routed to a tier, priced from usage.

Ties together the three levers:
  - router: cheap tier for classify/summarize, strong tier for draft (T2/01 pattern)
  - measurement: real usage from every converse call
  - the report sums USD and shows where the money actually goes
"""

from dataclasses import dataclass
from typing import Literal

from config import bedrock_client, settings
from cost import TokenCounts, cost_of

TaskType = Literal["classify", "summarize", "draft"]

ROUTES: dict[TaskType, str] = {
    "classify": settings.cheap_model_id,
    "summarize": settings.cheap_model_id,
    "draft": settings.strong_model_id,
}

PROMPTS: dict[TaskType, str] = {
    "classify": "Ordne einer Kategorie zu, antworte mit genau einem Wort:",
    "summarize": "Fasse in einem Satz zusammen:",
    "draft": "Formuliere eine höfliche Antwort-E-Mail auf:",
}


@dataclass
class LineItem:
    task_type: TaskType
    model_id: str
    cost_usd: float


def run_task(task_type: TaskType, text: str) -> LineItem:
    model_id = ROUTES[task_type]
    response = bedrock_client().converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": f"{PROMPTS[task_type]}\n{text}"}]}],
        inferenceConfig={"maxTokens": 200, "temperature": 0},
    )
    usage = response["usage"]
    tokens = TokenCounts(input_tokens=usage["inputTokens"], output_tokens=usage["outputTokens"])
    return LineItem(task_type, model_id, cost_of(model_id, tokens).total)


def cost_report(workload: list[tuple[TaskType, str]]) -> list[LineItem]:
    return [run_task(task_type, text) for task_type, text in workload]


def total_cost(items: list[LineItem]) -> float:
    return sum(item.cost_usd for item in items)


if __name__ == "__main__":
    workload: list[tuple[TaskType, str]] = [
        ("classify", "Meine Kreditkarte wurde doppelt belastet."),
        ("classify", "Wann öffnet das Hotel-Restaurant?"),
        ("summarize", "Der Flug war pünktlich, das Hotel sauber, der Transfer kam zu spät."),
        ("draft", "Kunde beschwert sich über den verspäteten Transfer."),
    ]
    items = cost_report(workload)
    for item in items:
        tier = "cheap" if item.model_id == settings.cheap_model_id else "STRONG"
        print(f"{item.task_type:10} [{tier:6}]  ${item.cost_usd:.6f}")
    print(f"\nGesamt: ${total_cost(items):.6f}")
