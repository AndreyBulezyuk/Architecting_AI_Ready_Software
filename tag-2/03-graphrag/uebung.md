# Übung T2/03 — Ontologie erweitern & GraphRAG gegen die Baseline

**Ziel:** Einmal selbst erleben, dass die Ontologie die eigentliche Design-Entscheidung ist — und schwarz auf weiß sehen, welche Dokumente nur der Graph erreicht.
**Zeit:** ~90 min. **Voraussetzung:** Demo T2/03 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **Ontologie**: Die Festlegung, welche Entity-Typen und Beziehungen euer Graph kennt (bei uns: `destination`/`activity`/`audience` + `MENTIONS`). Sie bestimmt, welche Fragen der Graph beantworten kann.
- **Graph-Expansion**: Der Schritt nach der Vektor-Suche — von den Treffer-Dokumenten über gemeinsame Entities zu verwandten Dokumenten laufen (eine Cypher-Query, kein LLM-Call).

## Teil 1 — Nachziehen (≈15 min)

Demo-Tests + `uv run python graphrag.py` ausführen. Schaut euch im Neo4j Browser an, welche Entities eure fünf Dokumente teilen — stimmt das mit eurem Bauchgefühl überein? Welche Entität hättet ihr erwartet, die fehlt?

## Teil 2 — Ontologie erweitern: `season` (≈35 min)

Reisen sind saisonal — der Graph weiß davon nichts. Ändert das (eigenes Projekt, Demo als Vorlage):

1. Erweitert das Extraktions-Schema um den Entity-Typ `season` (Werte wie `winter`, `sommer` — wo genau muss der neue Typ überall hin? Es sind **drei** Stellen: Pydantic-Modell, Prompt, nirgends im Graph-Code — warum eigentlich nicht?).
2. Schreibt einen sechsten Reisebericht mit klarem Saisonbezug (z. B. Ostsee im Winter) und ingestiert alle sechs neu.
3. Prüft per Cypher: Welche Dokumente hängen jetzt über eine `season`-Entität zusammen? ([Cypher MATCH-Doku](https://neo4j.com/docs/cypher-manual/current/clauses/match/))

**Recherche:** Was passiert mit euren alten `MENTIONS`-Kanten, wenn ihr ein Dokument erneut ingestiert — und warum löscht die Demo Entities beim Re-Ingest **nicht** mit? (Tipp: Wem "gehört" eine geteilte Entität?)

## Teil 3 — Baseline vs. GraphRAG, nebeneinander (≈30 min)

1. Baut `compare(question)`: schickt dieselbe Frage einmal durch reine Vektor-Suche (Top-5, ohne Expansion) und einmal durch euren GraphRAG-Pfad; Rückgabe: beide Antworten + beide Dokument-Mengen.
2. Nehmt eure **Multi-Hop-Frage aus der T2/02-Abschlussrunde** und mindestens zwei weitere Fragen. Für welche Fragen sind die Dokument-Mengen identisch — und für welche holt der Graph mehr?
3. Notiert die Fragen samt erwarteter "guter" Antwort — das ist euer **Eval-Datensatz für Tag 3** (Ragas entscheidet dann, ob GraphRAG die Baseline wirklich schlägt).

## Zusatzaufgabe (schnelle Teilnehmer)

Lest die [neo4j-graphrag-Doku](https://neo4j.com/docs/neo4j-graphrag-python/current/) (SimpleKGPipeline + Retriever): Welche eurer heutigen Handgriffe automatisiert die Bibliothek — und welche Entscheidung nimmt sie euch **nicht** ab?

## Abschlussfragen

1. Ingest kostet jetzt einen LLM-Call pro Dokument. Bei welcher Korpusgröße und Änderungsrate kippt das Kosten-Nutzen-Verhältnis — und welches Muster aus Kapitel 04/05 begrenzt den Schaden?
2. Die `via`-Herkunft macht Kontext erklärbar. Wem in eurer Organisation zeigt ihr diese Information — und in welcher Form?

## Hinweise

- Label-Präfix beibehalten (`T3…`) oder eigenes wählen — die lokale Neo4j ist geteilt.
- Lösung in `loesung/` — erst nach eigenem Versuch.
