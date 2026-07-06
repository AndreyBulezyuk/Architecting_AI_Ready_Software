# Demo 04 — Event-Pipeline: Bus → Rule → Queue → Worker → DLQ

Ablauf (~15 min). Erst in AWS (Primärweg), dann derselbe Code als pytest gegen LocalStack.

```bash
cd tag-1/04-event-driven-ki-workloads/demo
uv sync

# --- Teil 1: gegen AWS (SSO-Login aus Kapitel 03 aktiv) ---
export AWS_PROFILE=training
uv run python infra.py                       # Bus, Rule, Queue + DLQ, Queue-Policy
uv run python producer.py "hotel am meer"    # Event publizieren
uv run python worker.py                      # Event empfangen, validieren, löschen

# Gift-Nachricht: direkt (ohne Envelope) in die Queue → landet nach 2 Versuchen in der DLQ
QURL=$(aws sqs get-queue-url --queue-name t04-demo-profile-events --query QueueUrl --output text)
aws sqs send-message --queue-url "$QURL" --message-body '{"detail": {"broken": true}}'
uv run python worker.py   # mehrfach ausführen, dann DLQ prüfen:
aws sqs receive-message --queue-url $(aws sqs get-queue-url --queue-name t04-demo-profile-events-dlq --query QueueUrl --output text)

# --- Teil 2: identischer Code als Test gegen LocalStack (docker compose up -d) ---
uv run pytest -v
```

**Wichtige Punkte:**

- [infra.py](infra.py) setzt die **Queue-Policy** für EventBridge → in AWS Pflicht, LocalStack erzwingt sie nicht (Folie 6).
- [worker.py](worker.py) löscht Nachrichten erst **nach** erfolgreicher Verarbeitung — Validierungsfehler führen automatisch über Retry in die DLQ.
- [models.py](models.py): Event-Schema mit `event_version` und `event_id` von Anfang an (Folie 5).
- Infra per boto3 ist hier bewusst "Handarbeit" — in der Übung wandert sie in den CDK-Stack.
