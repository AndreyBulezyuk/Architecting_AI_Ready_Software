# Übung T3/02 — Ist GraphRAG wirklich besser? Messt es.

**Ziel:** Die T2/02-Baseline und das T2/03-GraphRAG auf denselben Fragen mit Ragas bewerten — und die Behauptung "GraphRAG liefert bessere Antworten" (die seit Tag 2 im Raum steht) zum ersten Mal an echten Zahlen prüfen.
**Zeit:** ~90 min. **Voraussetzung:** Demo T3/02 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **LLM-as-Judge**: Ein zweites LLM bewertet die Antwort des ersten — hier übernimmt das Bedrock-Modell aus `ragas_bedrock.py` die Rolle des Prüfers, nicht des Antwortenden.
- **Faithfulness, Context Precision, Context Recall**: siehe Demo-README — kurz: "steht drin, was behauptet wird?", "ist der Kontext relevant?", "deckt der Kontext die Antwort vollständig ab?".

## Teil 1 — Nachziehen (≈15 min)

Demo-Tests + `uv run python evaluate.py` ausführen. Verändert **eine** Referenzantwort in `eval_dataset.py` bewusst falsch (z. B. eine Zahl ändern) und beobachtet: Welche Metrik reagiert darauf — Faithfulness oder Context Recall? Warum genau die?

## Teil 2 — Baseline vs. GraphRAG selbst messen (≈45 min)

Baut euer eigenes Vergleichsprojekt (Vorlage: T2/03-Demo für den 5-Dokumente-Korpus mit `madeira`/`gardasee`):

1. Übernehmt `kg.py`/`graphrag.py` aus eurer T2/03-Lösung (oder der Demo) — **eigene Neo4j-Labels** wählen, sonst kollidiert ihr mit bereits vorhandenen Daten in der geteilten lokalen Neo4j.
2. Schreibt `baseline_answer(question, k)`: dieselbe Retrieval-Funktion wie GraphRAG, aber **ohne** `graph_expansion()` — nur `vector_hits()`. Das ist eure faire Baseline (gleiches Embedding-Modell, gleicher Prompt, gleiches `k` wie GraphRAG).
3. Stellt einen kleinen Fragenkatalog mit Referenzantworten zusammen (3–4 Fragen zum 5-Dokumente-Korpus) — nutzt gern eure Fragen aus der T2/03-Abschlussrunde.
4. Bewertet **beide** Antwort-Pfade mit **denselben** Ragas-Metrik-Instanzen (ein `Faithfulness`, ein `ContextPrecision`, ein `ContextRecall` — nicht für jeden Pfad neue Instanzen bauen, sonst ist der Vergleich nicht fair).

**Schreibt euer Ergebnis auf, bevor ihr weiterlest.** Gewinnt GraphRAG? Verliert es? Unentschieden?

## Teil 3 — Warum, und wann wäre es anders? (≈30 min)

1. Schaut euch für eine Frage den **Kontext** beider Pfade konkret an (`context`-Liste, nicht nur den Score): Wie viele Dokumente holt die Baseline mit `k=3` bei nur 5 Dokumenten im Korpus insgesamt? Was bedeutet das für den Spielraum, den die Graph-Expansion überhaupt noch hat?
2. **Experiment:** Setzt `k=1` für **beide** Pfade (Baseline UND GraphRAG-Einstieg) und wiederholt die Messung. Ändert sich der Abstand zwischen Baseline und GraphRAG? Warum sollte `k` das Ergebnis überhaupt beeinflussen?
3. Konstruiert **eine** neue Frage, bei der ihr **vorher begründet erwartet**, dass nur GraphRAG sie vollständig beantworten kann (Tipp: eine Antwort, die Fakten aus zwei Dokumenten kombiniert, die bei `k=1` oder `k=2` **nicht beide** unter den Top-Treffern wären). Messt nach — hattet ihr recht?

## Abschlussfragen

1. Formuliert in einem Satz, **unter welcher Bedingung** sich der Mehraufwand von GraphRAG (LLM-Call pro Dokument beim Ingest, Kapitel T2/03) lohnt — und unter welcher nicht.
2. Ihr habt jetzt zwei Zahlen für "gut": Hit-Rate@k (T2/02, misst Retrieval) und Faithfulness/Context-Recall (heute, misst die ganze Antwort). Was hätte eine hohe Hit-Rate, aber niedrige Faithfulness zu bedeuten — an welcher Stelle der Pipeline würdet ihr suchen?

## Hinweise

- Kein Metrik-Ergebnis ist "das richtige" — Ragas' LLM-Judge hat bei `temperature=0` zwar wenig, aber nicht null Varianz. Lauft eure Messung bei Unklarheit zweimal.
- Lösung in `loesung/` — dort steht auch das gemessene Ergebnis dieser Schulung als Referenz. Schaut **erst nach eigener Messung** nach.
