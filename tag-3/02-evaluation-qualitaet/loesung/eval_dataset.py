"""Eval dataset for the Baseline-vs-GraphRAG comparison — the multi-hop question
comes straight from T2/03's theory slide 2 ("Warum ein Graph?").

Madeira alone already answers "wandern UND baden" — the interesting case is a
question where the answer is SPREAD across two documents that only the graph
expansion connects (an activity or destination trait no single doc fully covers).
"""

EVAL_QUESTIONS: list[tuple[str, str]] = [
    (
        "Wo kann ich wandern und danach im Meer baden?",
        "Auf Madeira: vormittags an den Levadas wandern, abends in den "
        "Naturpools von Porto Moniz im Atlantik baden.",
    ),
    (
        "Welches Ziel eignet sich für eine Wandertour mit Übernachtung in einer Hütte?",
        "Die Stubaier Alpen: eine siebentägige Hüttentour mit 800 bis 1200 "
        "Höhenmetern pro Tag, Übernachtung im Lager.",
    ),
    (
        "Wo kann man wandern und ist gleichzeitig für Familien mit Kindern geeignet?",
        "Am Gardasee: Radtouren am Ufer und die Seilbahn auf den Monte Baldo mit "
        "Panoramawegen für jedes Niveau, dazu Baden am Kiesstrand — familienfreundlich "
        "organisierte Campingplätze.",
    ),
]
