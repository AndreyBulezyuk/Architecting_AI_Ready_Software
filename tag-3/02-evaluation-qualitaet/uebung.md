# Übung T3/02 — Ist GraphRAG wirklich besser? Messt es.

**Ziel:** Die T2/02-Baseline und das T2/03-GraphRAG auf denselben Fragen mit Ragas bewerten — und die Behauptung "GraphRAG liefert bessere Antworten" (die seit Tag 2 im Raum steht) zum ersten Mal an echten Zahlen prüfen.
**Zeit:** ~90 min. **Voraussetzung:** Demo T3/02 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **LLM-as-Judge**: Ein zweites LLM bewertet die Antwort des ersten — hier übernimmt das Bedrock-Modell aus `ragas_bedrock.py` die Rolle des Prüfers, nicht des Antwortenden.
- **Faithfulness, Context Precision, Context Recall**: siehe Demo-README — kurz: "steht drin, was behauptet wird?", "ist der Kontext relevant?", "deckt der Kontext die Antwort vollständig ab?".

## Teil 1 — Nachziehen (≈15 min)

Demo-Tests + `uv run python evaluate.py` ausführen. Verändert **eine** Referenzantwort in `eval_dataset.py` bewusst falsch (z. B. eine Zahl ändern) und beobachtet: Welche Metrik reagiert darauf — Faithfulness oder Context Recall? Warum genau die?

## Teil 2 — Baseline vs. GraphRAG selbst messen (≈45 min)

Vorlage: die T2/03-Demo (5-Dokumente-Korpus mit `madeira`/`gardasee`). Vier Schritte, jeder mit klarem Ziel:

**Schritt 1 — Ziel:** `kg.py`/`graphrag.py` aus eurer T2/03-Lösung (oder der Demo) übernehmen und den Graphen aufbauen.
**Schritt 1 — Tipp:** Wählt **eigene Neo4j-Labels** (z. B. `EvalDoc`), sonst kollidiert ihr mit bereits vorhandenen Daten in der geteilten Neo4j.

**Schritt 2 — Ziel:** Eine faire Baseline bauen — `baseline_answer(question, k)` nutzt dasselbe Retrieval wie GraphRAG, aber **ohne** `graph_expansion()`.
**Schritt 2 — Tipp:** Nur `vector_hits()` aufrufen und denselben Prompt, dasselbe Embedding-Modell und dasselbe `k` wie GraphRAG verwenden — sonst vergleicht ihr zwei Änderungen auf einmal.

**Schritt 3 — Ziel:** Einen kleinen Prüf-Datensatz zusammenstellen — 3–4 Fragen mit je einer Referenzantwort.
**Schritt 3 — Tipp:** Nehmt die Fragen aus eurer T2/03-Abschlussrunde; die Referenzantwort ist die „richtige" Antwort, gegen die Ragas misst.

**Schritt 4 — Ziel:** Beide Pfade mit Ragas bewerten und die Zahlen vergleichen.
**Schritt 4 — Tipp:** Für beide Pfade **dieselben** Metrik-Instanzen benutzen (ein `Faithfulness`, ein `ContextPrecision`, ein `ContextRecall`) — neue Instanzen pro Pfad verfälschen den Vergleich. Siehe [Ragas Metrics](https://docs.ragas.io/en/stable/concepts/metrics/).

**Schreibt euer Ergebnis auf, bevor ihr weiterlest.** Gewinnt GraphRAG, verliert es, oder ist es unentschieden?

## Teil 3 — Warum, und wann wäre es anders? (≈30 min)

**Schritt 1 — Ziel:** Verstehen, warum der Unterschied klein sein kann — den tatsächlichen `context` beider Pfade ansehen (nicht nur den Score).
**Schritt 1 — Tipp:** Zählt, wie viele Dokumente die Baseline mit `k=3` bei nur 5 Dokumenten im Korpus schon holt. Viel Spielraum bleibt der Graph-Expansion dann nicht.

**Schritt 2 — Ziel:** Den Effekt von `k` messen — `k=1` für **beide** Pfade setzen und die Bewertung aus Teil 2 wiederholen.
**Schritt 2 — Tipp:** Vergleicht den Abstand Baseline↔GraphRAG bei `k=1` mit dem bei `k=3`. Je kleiner `k`, desto mehr muss die Graph-Expansion leisten.

**Schritt 3 — Ziel:** Einen Fall konstruieren, in dem GraphRAG gewinnen **muss**, und die Vorhersage prüfen.
**Schritt 3 — Tipp:** Baut eine Frage, deren Antwort Fakten aus **zwei** Dokumenten kombiniert, die bei `k=1`/`k=2` nicht beide unter den Top-Treffern wären. Erst begründen, was ihr erwartet — dann messen.

## Abschlussfragen

1. Formuliert in einem Satz, **unter welcher Bedingung** sich der Mehraufwand von GraphRAG (LLM-Call pro Dokument beim Ingest, Kapitel T2/03) lohnt — und unter welcher nicht.
2. Ihr habt jetzt zwei Zahlen für "gut": Hit-Rate@k (T2/02, misst Retrieval) und Faithfulness/Context-Recall (heute, misst die ganze Antwort). Was hätte eine hohe Hit-Rate, aber niedrige Faithfulness zu bedeuten — an welcher Stelle der Pipeline würdet ihr suchen?

## Hinweise

- Kein Metrik-Ergebnis ist "das richtige" — Ragas' LLM-Judge hat bei `temperature=0` zwar wenig, aber nicht null Varianz. Lauft eure Messung bei Unklarheit zweimal.
- Lösung in `loesung/` — dort steht auch das gemessene Ergebnis dieser Schulung als Referenz. Schaut **erst nach eigener Messung** nach.
