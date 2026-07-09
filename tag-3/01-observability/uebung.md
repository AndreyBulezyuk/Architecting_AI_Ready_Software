# Übung T3/01 — Den T2/05-Agenten tracen

**Ziel:** Erleben, dass ein Agent-Framework Beobachtbarkeit oft schon eingebaut hat — und die eine Lücke schließen, die selbst dann bleibt: mehrere Agent-Läufe zu einer Nutzer-Session zusammenzuführen.
**Zeit:** ~60 min. **Voraussetzung:** Demo T3/01 gesehen; Neo4j läuft, Langfuse läuft (`docker compose --profile observability up -d`), AWS-Profil aktiv.

**Begriff für diese Übung:**

- **Session** (in Langfuse): mehrere zusammenhängende Traces (z. B. mehrere Fragen eines Nutzers in einem Chat) werden über `session.id` zu einer Gruppe verbunden — ohne `session.id` sieht Langfuse nur einzelne, unverbundene Traces.

## Teil 1 — Nachziehen (≈15 min)

1. In eurem T2/05-Projekt (oder einer Kopie davon): `uv add opentelemetry-sdk opentelemetry-exporter-otlp-proto-http`.
2. Baut `StrandsTelemetry().setup_otlp_exporter(endpoint=..., headers=...)` auf (Muster: Demo-`tracing.py`, `endpoint` zeigt auf `http://localhost:3000/api/public/otel/v1/traces`, Basic-Auth wie in der Demo).
3. Ruft euren Agenten **ohne jede weitere Änderung** an `assistant.py` auf und schaut in Langfuse nach: Was seht ihr im Trace-Baum? **Recherche:** Was ist die Wurzel-Observation, welchen Typ hat sie, und welche Kind-Observations gibt es? (Kein Rätsel — einfach nachschauen.)

## Teil 2 — Die eine Lücke schließen: Sessions (≈25 min)

Auch mit Strands' Auto-Instrumentierung bleibt eine Frage offen: Gehören zwei aufeinanderfolgende `agent(frage)`-Aufrufe zusammen?

1. Schreibt `ask(question, session_id, tags)`: öffnet **euren eigenen** Root-Span um den `agent(...)`-Aufruf, setzt `session.id` und `langfuse.trace.tags` darauf.
2. Ruft `ask()` **zweimal nacheinander** mit derselben `session_id`, aber unterschiedlichen Fragen auf.
3. Prüft in Langfuse: Landen beide Traces mit derselben `sessionId`? Sind die Strands-eigenen Spans (AGENT, TOOL, GENERATION) weiterhin korrekt verschachtelt **unterhalb** eures Wrapper-Spans?

**Recherche:** Warum reicht ein einfacher `with`-Block, damit die Strands-Spans automatisch als Kinder eures Spans landen — wo genau wird die Parent-Child-Beziehung weitergegeben? (Stichwort: OTel Context Propagation, `contextvars`.)

## Teil 3 — Ein zweites Tool, ein zweiter Blick (≈20 min)

1. Gebt dem Agenten ein zweites eigenes Tool (z. B. `current_season(month: int)` aus T2/05 Übung, falls vorhanden — sonst neu schreiben).
2. Stellt eine Frage, die **beide** Tools braucht, und prüft: Bekommt auch euer selbst geschriebenes Tool automatisch einen `TOOL`-Span — oder müsst ihr dafür etwas extra tun?
3. Schreibt einen Test, der über die Langfuse-API beweist: Trace enthält mindestens zwei `TOOL`-Observations mit den erwarteten Namen.

## Abschlussfragen

1. Bei T2/04 (`rag.py`) musstet ihr jeden Span von Hand schreiben, heute beim Agenten fast keinen. Woran liegt der Unterschied — was genau übernimmt Strands, was RAG-Code wie `rag.py` nicht "geschenkt" bekommt?
2. Euer Service aus T2/04 hat `request_id` als Vertragsfeld. Der Agent hat jetzt `session.id`. Sind das dieselbe Art von Identifikator? Wo würdet ihr `session_id` in einer echten Chat-Anwendung herbekommen (Hinweis: nicht neu erfinden — wo entsteht so eine ID normalerweise schon)?

## Hinweise

- `StrandsTelemetry()` beim zweiten Aufruf im selben Prozess erneut aufzurufen fügt einen weiteren Exporter hinzu — in eigenen Skripten nur **einmal** konfigurieren (z. B. beim Modulimport wie in der Lösung).
- Lösung in `loesung/` — erst nach eigenem Versuch.
