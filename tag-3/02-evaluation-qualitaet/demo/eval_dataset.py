"""Eval dataset for the T2/02 Vector-RAG baseline: (question, reference answer).

The reference answers are written by hand from SAMPLE_DOCS — this is exactly the
"Fragenkatalog mit erwarteter Antwort" the T2/02 and T2/03 exercises already asked
you to collect. Ragas needs a reference to compute context_precision/context_recall
(it checks whether the retrieved context COULD have produced this reference).
"""

EVAL_QUESTIONS: list[tuple[str, str]] = [
    (
        "Wo kann man mit Kindern baden?",
        "An der Algarve, in den flachen und geschützten Buchten bei Lagos.",
    ),
    (
        "Wie anstrengend ist die Hüttentour in den Alpen?",
        "Sehr anstrengend: 800 bis 1200 Höhenmeter pro Tag, Trittsicherheit ist Pflicht.",
    ),
    (
        "Wie kommt man in Tokio am besten von A nach B?",
        "Mit der U-Bahn, die im Minutentakt fährt, und mit der IC-Karte für Bahn und Automaten.",
    ),
]
