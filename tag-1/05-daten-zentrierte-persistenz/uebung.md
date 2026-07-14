# Übung 05 — Event-getriebenes Re-Embedding + Index-Beweis

**Ziel:** Den Embedding-Lifecycle aus der Demo mit den Events aus Kapitel 04 verbinden — und per `SHOW VECTOR INDEXES` beweisen, dass euer Vektor-Index wirklich arbeitet.
**Zeit:** ~75 min. **Voraussetzung:** Demo 05 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **`stale`** (dt. "veraltet"): Die Quelle in S3 wurde geändert, aber das Embedding in Neo4j ist noch der alte Stand — bis zum Re-Embed fliegt das Dokument aus den Suchtreffern.
- **Top-k-Suche**: "Gib mir die `k` ähnlichsten Knoten zum Query-Vektor." Der Index nutzt eine vorab aufgebaute Nachbarschaftsstruktur (ANN, Approximate Nearest Neighbor), statt alle Vektoren zu vergleichen — schnell auch bei großen Beständen.
- **`state` / `populationPercent`** (aus `SHOW VECTOR INDEXES`): pflegt Neo4j **automatisch** — `state` ist der Index-Lebenszyklus (`POPULATING` → `ONLINE`, im Fehlerfall `FAILED`), `populationPercent` der Fortschritt des Index-Aufbaus in Prozent. Ihr berechnet hier nichts selbst, ihr lest nur ab.

## Teil 1 — Nachziehen (≈10 min)

Demo-Tests ausführen und den REPL-Ablauf aus dem [Demo-README](demo/README.md) einmal selbst durchspielen. Achtet auf den Moment, in dem `search` nichts findet — warum ist das **richtig**?

## Teil 2 — Re-Embed wird event-getrieben (≈35 min)

In der Demo stößt man `reembed_stale()` von Hand an. Baut das um (eigenes Projekt, Demo als Vorlage):

1. Neues Event `DocumentUpdated` (Pydantic, v1, `event_id`, `document_id`) — Konventionen aus Kapitel 04.
2. `upsert_document` schickt nach dem Schreiben eine `DocumentUpdated`-Nachricht in eine SQS-Queue `t05-ueb-doc-updated` (direkt via `send_message`, ohne Bus — wann reicht das? → Abschlussfrage).
3. Ein Worker konsumiert die Queue und re-embedded **genau das eine** Dokument (`reembed_document(document_id)`), statt alle stale-Zeilen zu scannen.
4. Test: Dokument einfügen → Event verarbeiten → Suche findet es. Update → Suche verliert es → Event verarbeiten → wieder da.

**Recherche:** Was passiert bei eurem Worker, wenn das Dokument zwischen Event und Verarbeitung schon wieder geändert wurde? (Tipp: `embedding_stale` nach dem Embedden nur zurücksetzen, wenn sich `updated_at` nicht geändert hat — oder bewusst ignorieren und begründen.)

## Teil 3 — Beweist, dass der Index arbeitet (≈20 min)

1. Füllt den Store per Schleife mit ~30 generierten Dokumenten (Events verarbeiten nicht vergessen!).
2. Prüft den Index-Zustand: [`SHOW VECTOR INDEXES`](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/) — welchen `state` und `populationPercent` erwartet ihr, und was seht ihr direkt nach einem großen Schreib-Burst?
3. Fragt die Top-5 ab und schaut euch die `score`-Werte an. **Recherche:** Ist `score` eine Distanz oder eine Ähnlichkeit — und was bedeutet das für eure Sortierung?

## Abschlussfragen

1. SQS direkt vs. EventBridge-Bus + Rule (Kapitel 04): Wann reicht die nackte Queue?
2. Was kostet ein Re-Embed-Sturm (jemand importiert 40.000 Dokumente) — und welche zwei Stellschrauben aus Kapitel 04/05 begrenzen ihn? (Batching, Queue als Puffer)
3. Warum speichern wir `embedding_model` pro Zeile — welches konkrete Szenario rettet uns das?

## Hinweise

- Namenspräfix `t05-ueb-…`; Lösung in `loesung/` erst nach eigenem Versuch.
- Achtung, geteilte lokale Neo4j: pro Label+Property ist nur **ein** Vector Index erlaubt — nutzt ein eigenes Label (z. B. `UebDocument`), sonst kollidiert ihr mit der Demo.
- SQS-Queue und S3-Bucket liegen in eurem AWS-Account — am Ende `uv run python cleanup.py` (Wegwerf-Design).
