# Lösung 04

```bash
uv sync
uv run pytest -v            # gegen LocalStack (docker compose up -d)

# gegen AWS:
export AWS_PROFILE=training
uv run python infra.py && uv run python producer.py && uv run python worker.py
```

Stolpersteine aus der Übung:

- **Rule-Filter:** `detail-type` (mit Bindestrich!) im Event-Pattern — `{"source": ["travelmate"], "detail-type": ["BookingCreated"]}`.
- **Conditional Put:** `ConditionExpression="attribute_not_exists(event_id)"`; bei Verletzung fliegt `dynamodb.exceptions.ConditionalCheckFailedException` — das **ist** der Duplikat-Fall, kein Fehler.
- **Duplikate löschen wir aus der Queue** (Abschlussfrage 1): Sie sind erwartetes Verhalten von at-least-once — in der DLQ würden sie nur echte Gift-Nachrichten verwässern.
- Abschlussfrage 2: Crash zwischen Put und Verarbeitung ⇒ Event gilt als verarbeitet, wurde es aber nie (at-most-once). Reparatur: statt reiner Existenz ein Status-Feld (`claimed` → `done`) mit Timestamp + Aufräum-Job für hängende `claimed`-Einträge.
