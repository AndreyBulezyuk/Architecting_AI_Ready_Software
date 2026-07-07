"""Hit-rate evaluation for the chunking experiment (part 2)."""

from dataclasses import dataclass

import store

# question -> doc_id that contains the answer
QUESTIONS: list[tuple[str, str]] = [
    ("Wo kann man mit Kindern baden?", "algarve"),
    ("Wie anstrengend ist die Hüttentour?", "alpen"),
    ("Muss man Hütten vorab reservieren?", "alpen"),
    ("Wie kommt man in der Stadt von A nach B?", "tokio"),
    ("Wo gibt es günstige Kinderteller?", "algarve"),
]


@dataclass
class EvalResult:
    hits: int
    total: int

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total if self.total else 0.0


def hit_rate_at_k(
    questions: list[tuple[str, str]], k: int = 3, *, table_name: str | None = None
) -> EvalResult:
    hits = 0
    for question, expected_doc in questions:
        found = {hit.doc_id for hit in store.search(question, k=k, table_name=table_name)}
        if expected_doc in found:
            hits += 1
    return EvalResult(hits=hits, total=len(questions))
