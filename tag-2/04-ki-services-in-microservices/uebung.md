# Übung T2/04 — Euer Retrieval wird ein Service (sync + async)

**Ziel:** Die KI-Fähigkeit hinter einen versionierten API-Vertrag packen — und den asynchronen Integrationspfad bauen, den Chat-UIs nicht brauchen, aber Batch-Konsumenten sehr wohl.
**Zeit:** ~90 min. **Voraussetzung:** Demo T2/04 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **202 Accepted**: HTTP-Status für "Auftrag angenommen, Ergebnis kommt später" — der Vertrag verspricht Verarbeitung, keine Antwort.
- **Backpressure**: Überlast wird an den Aufrufer **weitergegeben** (503 + `Retry-After`) statt sie im Service zu verstecken — der Aufrufer entscheidet über Retry, Fallback oder Queue.

## Teil 1 — Nachziehen (≈15 min)

Demo starten (`uv run fastapi dev service.py`), unter <http://localhost:8000/docs> den Vertrag ansehen, Tests laufen lassen. Schaut euch an, **wie** der Throttling-Test funktioniert, ohne dass Bedrock wirklich drosselt (monkeypatch) — das Muster braucht ihr gleich.

## Teil 2 — Sync-Service um euer Retrieval (≈35 min)

Baut den Service in eurem Projekt — mit **eurem** Retrieval aus T2/02 oder T2/03 hinter der Naht (`rag.py`-Modul der Demo als Vorlage):

1. `POST /v1/ask` mit dem Vertrag aus der Demo (`schema_version`, `request_id`, `sources`, `refused`, Token-/Latenz-Metriken). Wer T2/03 einsetzt: gebt die `via`-Herkunft der Quellen mit — welchen Feldnamen wählt ihr dafür im Vertrag?
2. `GET /healthz`: prüft Neo4j, ruft **nie** Bedrock (warum? Folie 2). Testet beide Zustände — wie simuliert ihr "Neo4j weg", ohne den Container zu stoppen? (Tipp: monkeypatch auf eure `driver`-Funktion.)
3. Fehlerbild: Throttling → 503 + `Retry-After`; andere `ClientError` → 502; `refused` → **200**. Ein Test pro Fall.

**Recherche:** [HTTPException mit Headern](https://fastapi.tiangolo.com/tutorial/handling-errors/) — warum landet ein Header, den ihr auf dem `Response`-Parameter setzt, **nicht** in der Fehlerantwort?

## Teil 3 — Der Async-Pfad (≈35 min)

1. `POST /v1/ask-jobs` → **erst** Job als `pending` in eine DynamoDB-Tabelle, **dann** in eine SQS-Queue, Antwort `202` + `job_id`. (Was passiert bei umgekehrter Reihenfolge? Malt den Race auf.)
2. Ein `worker.py` konsumiert die Queue, ruft euer RAG und setzt den Job auf `done` + `answer`. **Achtung, Recherche:** `status` ist in DynamoDB-Update-Expressions ein [reserviertes Wort](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html).
3. `GET /v1/ask-jobs/{id}`: `pending`/`done`/`404`. End-to-End-Test: submit → pending → Worker → done.

## Zusatzaufgabe (schnelle Teilnehmer)

Idempotenz für den Async-Pfad: Der Consumer schickt dieselbe Frage doppelt ab. Entwurfsfrage — dedupliziert ihr (a) beim Submit (Frage-Hash als `job_id`?), (b) im Worker, oder (c) gar nicht? Begründet mit dem Kapitel-04-Muster.

## Abschlussfragen

1. Der Agent in Kapitel 05 wird euren Service als Tool aufrufen. Welche drei Eigenschaften eures Vertrags machen ihn agententauglich?
2. Wo würdet ihr den Service in eurer echten Landschaft deployen (Gateway, Mesh, AuthN) — und was daran ist KI-spezifisch? (Erwartete Antwort: fast nichts.)

## Hinweise

- Ressourcen-Präfix `t204-<name>-…`; am Ende `uv run python cleanup.py` (Queue + Tabelle).
- Lösung in `loesung/` — erst nach eigenem Versuch.
