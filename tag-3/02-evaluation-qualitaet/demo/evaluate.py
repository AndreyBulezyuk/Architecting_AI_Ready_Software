"""Run the eval dataset through the RAG baseline, score every answer with Ragas.

Run: uv run python evaluate.py
"""

# ragas' metric classes ship partially-typed .score() members; results are
# consumed through our own typed EvalResult instead
# pyright: reportUnknownMemberType=false

from dataclasses import dataclass

from eval_dataset import EVAL_QUESTIONS
from ragas.metrics.collections import ContextPrecision, ContextRecall, Faithfulness
from ragas_bedrock import bedrock_judge

import rag
import store


@dataclass
class EvalResult:
    question: str
    faithfulness: float
    context_precision: float
    context_recall: float


def evaluate_baseline() -> list[EvalResult]:
    judge = bedrock_judge()
    faithfulness = Faithfulness(llm=judge)
    context_precision = ContextPrecision(llm=judge)
    context_recall = ContextRecall(llm=judge)

    results: list[EvalResult] = []
    for question, reference in EVAL_QUESTIONS:
        rag_answer = rag.answer(question)
        contexts = [hit.text for hit in rag_answer.sources]

        results.append(
            EvalResult(
                question=question,
                faithfulness=faithfulness.score(
                    user_input=question,
                    response=rag_answer.text,
                    retrieved_contexts=contexts,
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


def print_report(results: list[EvalResult]) -> None:
    for result in results:
        print(
            f"{result.question}\n"
            f"  faithfulness={result.faithfulness:.2f}  "
            f"context_precision={result.context_precision:.2f}  "
            f"context_recall={result.context_recall:.2f}"
        )
    n = len(results)
    print(
        f"\nDurchschnitt: faithfulness={sum(r.faithfulness for r in results) / n:.2f}  "
        f"context_precision={sum(r.context_precision for r in results) / n:.2f}  "
        f"context_recall={sum(r.context_recall for r in results) / n:.2f}"
    )


if __name__ == "__main__":
    store.init_schema()
    from sample_docs import SAMPLE_DOCS

    for doc_id, text in SAMPLE_DOCS.items():
        store.ingest_document(doc_id, text)

    print_report(evaluate_baseline())
