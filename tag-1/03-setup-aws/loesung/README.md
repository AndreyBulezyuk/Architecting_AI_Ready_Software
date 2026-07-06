# Lösung 03

```bash
uv sync
npx cdk synth        # offline prüfbar
npx cdk diff         # gegen den Account (SSO-Login nötig)
npx cdk deploy Participant
```

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
