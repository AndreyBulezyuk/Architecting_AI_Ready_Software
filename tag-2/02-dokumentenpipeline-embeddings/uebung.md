# Übung T2/02 — Chunking messen & die RAG-Baseline fertigbauen

**Ziel:** Retrieval-Qualität **messen** statt raten — und die Vector-RAG-Baseline bauen, gegen die morgen GraphRAG antreten muss.
**Zeit:** ~90 min. **Voraussetzung:** Demo T2/02 gesehen; Postgres läuft; AWS-Profil aktiv.

## Teil 1 — Nachziehen (≈10 min)

Demo-Tests + REPL-Ablauf ausführen. Probiert zwei eigene Queries ohne Wortüberlappung — wo liegt die Cosine-Distanz eines Treffers, wo die eines Nicht-Treffers?

## Teil 2 — Chunking-Experiment mit Hit-Rate (≈35 min)

Bauchgefühl durch Messung ersetzen:

1. Schreibt einen **Mini-Fragenkatalog**: 5 Fragen, jede mit dem `doc_id`, der die Antwort enthält (z. B. *"Wo kann man mit Kindern baden?"* → `algarve`). Nehmt gern 1–2 eigene Dokumente dazu.
2. Implementiert `hit_rate(questions, k)`: Anteil der Fragen, bei denen der erwartete `doc_id` in den Top-k-Treffern vorkommt.
3. Ingestiert den Korpus **zweimal** in getrennte Tabellen: einmal mit `max_chars=600, overlap=100` (Demo-Werte), einmal mit `max_chars=150, overlap=0`. Vergleicht die Hit-Rate@3 — und schaut euch an, *welche* Chunks bei der schlechteren Konfiguration gefunden werden.

**Recherche:** Warum kann ein sehr kleiner Chunk eine hohe Ähnlichkeit haben und trotzdem eine nutzlose Antwortgrundlage sein? (Folie 3 hilft.)

## Teil 3 — RAG-Antwort mit Zitaten und ehrlichem Scheitern (≈35 min)

1. `answer(question, k=3)`: Top-k-Chunks holen, als **nummerierten Kontext** (`[1]`, `[2]` …) in einen User-Prompt bauen, mit Haiku beantworten (Muster aus T2/01: `temperature=0`, System-Prompt mit Regeln).
2. Die Regeln im System-Prompt: nur aus dem Kontext antworten, Quellen als `[n]` zitieren — und wenn der Kontext die Frage **nicht** beantwortet, exakt mit `KEINE_ANTWORT_IM_KONTEXT` antworten.
3. Gebt neben dem Text auch die verwendeten Chunk-Referenzen zurück (`doc_id`, `seq`) — die API-Konsumenten von morgen brauchen sie.
4. Testet beides: eine beantwortbare Frage (Zitat vorhanden?) und *"Welche Programmiersprache ist die beste?"* (kommt der Marker?).

## Zusatzaufgabe (schnelle Teilnehmer)

Verwendet beim Query-Embedding absichtlich `search_document` statt `search_query` und messt die Hit-Rate erneut. Messbar schlechter? (Genau deshalb ist `input_type` Architektur und kein Detail.)

## Abschlussfragen

1. Eure Hit-Rate misst Retrieval. Was misst sie **nicht**? (Vorschau Tag 3: Ragas mit Faithfulness/Answer Relevancy.)
2. Formuliert eine Frage über den Korpus, die Vector-RAG **prinzipiell** schlecht beantwortet (Multi-Hop/Aggregation) — die nehmt ihr morgen mit ins GraphRAG-Kapitel.

## Hinweise

- Tabellen-Präfix `t202_ueb_…`, damit Demo- und Übungsdaten getrennt bleiben.
- Lösung in `loesung/` — erst nach eigenem Versuch.
