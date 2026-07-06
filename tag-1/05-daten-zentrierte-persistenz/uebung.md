# Übung 05 — Event-getriebenes Re-Embedding + Index-Beweis

**Ziel:** Den Embedding-Lifecycle aus der Demo mit den Events aus Kapitel 04 verbinden — und per `EXPLAIN` beweisen, dass euer Vektor-Index wirklich arbeitet.
**Zeit:** ~75 min. **Voraussetzung:** Demo 05 gesehen; lokaler Stack läuft.

## Teil 1 — Nachziehen (≈10 min)

Demo-Tests ausführen und den REPL-Ablauf aus dem [Demo-README](demo/README.md) einmal selbst durchspielen. Achtet auf den Moment, in dem `search` nichts findet — warum ist das **richtig**?

## Teil 2 — Re-Embed wird event-getrieben (≈35 min)

In der Demo stößt man `reembed_stale()` von Hand an. Baut das um (eigenes Projekt, Demo als Vorlage):

1. Neues Event `DocumentUpdated` (Pydantic, v1, `event_id`, `document_id`) — Konventionen aus Kapitel 04.
2. `upsert_document` schickt nach dem Schreiben eine `DocumentUpdated`-Nachricht in eine SQS-Queue `t05-ueb-doc-updated` (direkt via `send_message`, ohne Bus — wann reicht das? → Abschlussfrage).
3. Ein Worker konsumiert die Queue und re-embedded **genau das eine** Dokument (`reembed_document(document_id)`), statt alle stale-Zeilen zu scannen.
4. Test: Dokument einfügen → Event verarbeiten → Suche findet es. Update → Suche verliert es → Event verarbeiten → wieder da.

**Recherche:** Was passiert bei eurem Worker, wenn das Dokument zwischen Event und Verarbeitung schon wieder geändert wurde? (Tipp: `embedding_stale` nach dem Embedden nur zurücksetzen, wenn sich `updated_at` nicht geändert hat — oder bewusst ignorieren und begründen.)

## Teil 3 — Beweist, dass der Index benutzt wird (≈20 min)

1. Füllt die Tabelle mit ~200 generierten Dokumenten (Schleife reicht).
2. Holt euch den Query-Plan der Top-k-Suche: [`EXPLAIN`](https://www.postgresql.org/docs/current/sql-explain.html). Seht ihr einen `Index Scan using documents_embedding_hnsw` — oder einen `Seq Scan`?
3. Falls Seq Scan: Warum entscheidet der Planner so — und mit welchem Setting könnt ihr ihn zum Index zwingen, um den Unterschied zu sehen? ([Planner-Konfiguration](https://www.postgresql.org/docs/current/runtime-config-query.html))

## Abschlussfragen

1. SQS direkt vs. EventBridge-Bus + Rule (Kapitel 04): Wann reicht die nackte Queue?
2. Was kostet ein Re-Embed-Sturm (jemand importiert 40.000 Dokumente) — und welche zwei Stellschrauben aus Kapitel 04/05 begrenzen ihn? (Batching, Queue als Puffer)
3. Warum speichern wir `embedding_model` pro Zeile — welches konkrete Szenario rettet uns das?

## Hinweise

- Namenspräfix `t05-ueb-…`; Lösung in `loesung/` erst nach eigenem Versuch.
- Der `EXPLAIN`-Teil ist bewusst knifflig: Bei kleinen Tabellen gewinnt der Seq Scan zu Recht.
