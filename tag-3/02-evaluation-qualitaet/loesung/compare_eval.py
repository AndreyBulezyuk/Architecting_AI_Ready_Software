"""Score Vector-RAG-baseline vs. GraphRAG with Ragas on the SAME questions —
finally answering the question every Tag-2 chapter deferred: is GraphRAG actually
better, or does it just feel more sophisticated?

Run: uv run python compare_eval.py
"""

# ragas' metric classes ship partially-typed .score() members; results are
# consumed through our own typed ArmResult instead
# pyright: reportUnknownMemberType=false

from collections.abc import Callable
from dataclasses import dataclass

import graphrag
from eval_dataset import EVAL_QUESTIONS
from graphrag import GraphRagAnswer
from ragas.metrics.collections import ContextPrecision, ContextRecall, Faithfulness
from ragas_bedrock import bedrock_judge


@dataclass
class ArmResult:
    question: str
    faithfulness: float
    context_precision: float
    context_recall: float


def _score_arm(
    answer_fn: Callable[[str], GraphRagAnswer],
    faithfulness: Faithfulness,
    context_precision: ContextPrecision,
    context_recall: ContextRecall,
) -> list[ArmResult]:
    results: list[ArmResult] = []
    for question, reference in EVAL_QUESTIONS:
        rag_answer = answer_fn(question)
        contexts = [chunk.text for chunk in rag_answer.context]
        results.append(
            ArmResult(
                question=question,
                faithfulness=faithfulness.score(
                    user_input=question, response=rag_answer.text, retrieved_contexts=contexts
                ).value,
                context_precision=context_precision.score(
                    user_input=question, reference=reference, retrieved_contexts=contexts
                ).value,
                context_recall=context_recall.score(
                    user_input=question, retrieved_contexts=contexts, reference=reference
                ).value,
            )
        )
    return results


def compare() -> tuple[list[ArmResult], list[ArmResult]]:
    judge = bedrock_judge()
    faithfulness = Faithfulness(llm=judge)
    context_precision = ContextPrecision(llm=judge)
    context_recall = ContextRecall(llm=judge)

    baseline = _score_arm(graphrag.baseline_answer, faithfulness, context_precision, context_recall)
    graph = _score_arm(graphrag.answer, faithfulness, context_precision, context_recall)
    return baseline, graph


def _avg(results: list[ArmResult], field: str) -> float:
    return sum(getattr(r, field) for r in results) / len(results)


def print_report(baseline: list[ArmResult], graph: list[ArmResult]) -> None:
    for b, g in zip(baseline, graph, strict=True):
        print(f"\n{b.question}")
        print(
            f"  Baseline:  faithfulness={b.faithfulness:.2f}  "
            f"precision={b.context_precision:.2f}  recall={b.context_recall:.2f}"
        )
        print(
            f"  GraphRAG:  faithfulness={g.faithfulness:.2f}  "
            f"precision={g.context_precision:.2f}  recall={g.context_recall:.2f}"
        )
    print("\n--- Durchschnitt ---")
    for field in ("faithfulness", "context_precision", "context_recall"):
        print(f"{field}: Baseline={_avg(baseline, field):.2f}  GraphRAG={_avg(graph, field):.2f}")


if __name__ == "__main__":
    from store_setup import seed_corpus

    seed_corpus()
    print_report(*compare())
