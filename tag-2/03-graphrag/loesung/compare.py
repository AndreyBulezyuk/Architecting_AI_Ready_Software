"""Baseline vs. GraphRAG side by side (exercise part 3)."""

from dataclasses import dataclass

import graphrag


@dataclass
class Comparison:
    question: str
    vector_docs: set[str]
    graph_docs: set[str]
    graph_answer: str

    @property
    def graph_only_docs(self) -> set[str]:
        """Documents only the graph expansion reached — the GraphRAG win."""
        return self.graph_docs - self.vector_docs


def compare(question: str, k: int = 3) -> Comparison:
    vector_docs = {chunk.doc_id for chunk in graphrag.vector_hits(question, k)}
    result = graphrag.answer(question, k)
    return Comparison(
        question=question,
        vector_docs=vector_docs,
        graph_docs=result.doc_ids,
        graph_answer=result.text,
    )


if __name__ == "__main__":
    for question in (
        "Wo kann ich wandern und danach im Meer baden?",
        "Welche Ziele passen für Familien?",
    ):
        result = compare(question)
        print(f"\n{question}")
        print(f"  vector:     {sorted(result.vector_docs)}")
        print(f"  graph plus: {sorted(result.graph_only_docs)}")
