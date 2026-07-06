# Übung 04 — Zweiter Event-Typ, Routing und Idempotenz

**Ziel:** Die Demo-Pipeline um einen zweiten Event-Typ mit eigener Route erweitern und den Worker idempotent machen — die Grundlage für alles, was später LLM-Kosten verursacht.
**Zeit:** ~75 min. **Voraussetzung:** Demo 04 gesehen; Stack läuft (`docker compose up -d`); AWS-Profil aktiv.

## Teil 1 — Nachziehen (≈15 min)

Demo-Pipeline bei euch ausführen: in AWS (`infra.py` → `producer.py` → `worker.py`) **und** lokal (`uv run pytest -v` im Demo-Projekt). Schaut euch in der AWS-Konsole die Rule und die Queue-Policy an — die hat LocalStack euch geschenkt.

## Teil 2 — Zweiter Event-Typ mit eigener Route (≈25 min)

Baut in einem eigenen Projekt (Demo als Vorlage):

1. Neues Pydantic-Event `BookingCreated` (v1, `event_id`, `user_id`, `destination`, `price_eur`) — gleiche Envelope-Konventionen wie in der Demo.
2. Neue Queue `t04-ueb-booking-events` (+ eigene DLQ) und eine **eigene Rule** auf dem Demo-Bus, die **nur** `BookingCreated` dorthin routet.
3. Beweis in beide Richtungen: `BookingCreated` landet in der neuen Queue — und ein `SearchSubmitted` landet dort **nicht** (Filter wirkt).

**Recherche:** [EventBridge Event Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html) — wie filtert man auf `detail-type`?

## Teil 3 — Idempotenter Worker (≈30 min)

At-least-once heißt: Duplikate kommen. Macht die Verarbeitung idempotent:

1. DynamoDB-Tabelle `t04-ueb-processed-events` (Partition Key `event_id`).
2. Der Worker schreibt die `event_id` **vor** der Verarbeitung mit einem **Conditional Put** — nur wenn sie noch nicht existiert.
3. Publiziert dasselbe Event **zweimal** (gleiche `event_id`): Der Worker darf es nur **einmal** verarbeiten; das Duplikat wird erkannt, geloggt und trotzdem aus der Queue gelöscht (warum "trotzdem"? — Abschlussfrage).

**Recherche:** `ConditionExpression="attribute_not_exists(event_id)"` und welche Exception bei Verletzung fliegt ([Doku: Condition Expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)).

## Zusatzaufgabe (schnelle Teilnehmer)

Gießt die Übungs-Infrastruktur (Queues, Rule, Tabelle) in euren CDK-Stack aus Kapitel 03 — `aws_events.Rule` mit `aws_events_targets.SqsQueue` ([Doku](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/SqsQueue.html)). Schreibt einen Assertions-Test für die Rule.

## Abschlussfragen

1. Warum löschen wir erkannte Duplikate aus der Queue, statt sie in die DLQ laufen zu lassen?
2. Was passiert bei einem Crash **zwischen** Conditional Put und Verarbeitung? Welche Semantik hat unser Worker dann — und wie könnte man das reparieren (Stichwort: Status-Feld statt reiner Existenz)?
3. Welcher der beiden Event-Typen wird in Kapitel 06 das Benutzerprofil füttern — und welche Felder fehlen dafür noch?

## Hinweise

- Namenspräfix `t04-ueb-…` verwenden, damit ihr eure Ressourcen von der Demo unterscheiden könnt.
- Lösung in `loesung/` — erst nach eigenem Versuch.
