# Lösung 03

```bash
uv sync
npx cdk synth        # offline prüfbar
npx cdk diff         # gegen den Account (SSO-Login nötig)
npx cdk deploy Participant
```

## Woher kommt die Bedrock-Modell-ID?

Der [Converse-API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)-Call in [`bedrock_hello.py`](bedrock_hello.py) braucht in `eu-west-1` ein **[Inference Profile](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)** (Cross-Region, `eu.`-Präfix) — **nicht** die rohe Foundation-Model-ID. Rohe IDs (`anthropic.claude-…`) werden abgelehnt, ältere IDs wie `claude-3-haiku` sind als *Legacy* markiert und blockiert.

Aktive Claude-Profile für den Account auflisten und eine ID herauskopieren ([`list-inference-profiles`](https://docs.aws.amazon.com/cli/latest/reference/bedrock/list-inference-profiles.html)):

```bash
aws bedrock list-inference-profiles --profile default --region eu-west-1 \
    --query "inferenceProfileSummaries[?contains(inferenceProfileId, 'claude')].inferenceProfileId" \
    --output text
```

Aufbau der ID `eu.anthropic.claude-haiku-4-5-20251001-v1:0`:

| Segment | Bedeutung |
| --- | --- |
| `eu.` | Region-Scope des Cross-Region Inference Profile (`eu` = EU-Regionen) — genau dieses Präfix macht aus einer Foundation-Model-ID eine nutzbare Profile-ID |
| `anthropic` | Model Provider |
| `claude-haiku-4-5` | Modell-Familie + Tier (Haiku = günstigstes/schnellstes Claude) |
| `20251001` | Snapshot-Datum des Modells (`yyyymmdd`) |
| `v1:0` | Modell-Version |

Das Skript nutzt `eu.anthropic.claude-haiku-4-5-20251001-v1:0` als Default (günstigstes aktives Claude); per `export BEDROCK_MODEL_ID=…` überschreibbar. **Achtung:** Ein stale `BEDROCK_MODEL_ID` aus einem früheren Versuch überschreibt den Default still — im Zweifel `unset BEDROCK_MODEL_ID`. Das Skript druckt beim Start auf stderr, welche ID aus welcher Quelle (`env`/`default`) verwendet wird.

Stolpersteine aus der Übung:

- **DLQ:** Das gesuchte Argument ist `dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=…)` — die DLQ ist eine eigene, normale Queue.
- **`cdk bootstrap` vergessen** → Fehlermeldung "SSM parameter /cdk-bootstrap/... not found". Einmal pro Account+Region.
- **Bedrock:** `converse` schlägt mit `AccessDeniedException` fehl, solange Model Access nicht aktiviert ist; mit `ValidationException`, wenn das Modell in `eu-west-1` nur als Inference Profile (`eu.anthropic.…`) existiert und ihr die Basis-Modell-ID verwendet.

SQS-Beweis (Teil 2, Schritt 5):

```bash
QURL=$(aws ssm get-parameter --name /training/participant/queue-url --query Parameter.Value --output text)
aws sqs send-message --queue-url "$QURL" --message-body '{"job": "hello"}'
aws sqs receive-message --queue-url "$QURL"
```
