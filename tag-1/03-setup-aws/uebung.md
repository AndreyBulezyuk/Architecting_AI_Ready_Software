# Übung 03 — Eigener Account, eigener Stack, erster LLM-Call

**Ziel:** SSO-Zugang eingerichtet, eigenen CDK-Stack deployt (mit 2 Ressourcen mehr als die Demo) und den ersten Bedrock-Aufruf gemacht.
**Zeit:** ~75 min einzeln. **Voraussetzung:** Einladungs-Mail vom Identity Center ist angekommen.

## Teil 1 — Zugang (≈15 min)

1. Einladung annehmen, Passwort + MFA setzen, im Access Portal euren Account öffnen.
2. CLI koppeln: `aws configure sso` (Start-URL + Region nennt der Trainer), dann:

   ```bash
   aws sso login --profile training
   export AWS_PROFILE=training
   aws sts get-caller-identity   # eure Account-ID?
   ```

3. Bedrock **Model Access**: Console → Bedrock → *Model access* → Amazon-Nova-Modelle aktivieren (einzige Console-Aufgabe der Schulung).

## Teil 2 — Eigener Stack (≈40 min)

Baut auf der Demo auf, aber erweitert sie. Erstellt in eurem Projekt einen Stack `ParticipantStack` mit:

1. **S3-Bucket** wie in der Demo (`infrastructure/stacks/base_stack.py` als Vorlage).
2. **Neu: SQS-Queue** `ai-jobs` **mit Dead-Letter-Queue**: Nachrichten sollen nach 3 fehlgeschlagenen Empfängen in die DLQ wandern. **Recherche:** Wie heißt das Konstrukt-Argument? ([aws_sqs.Queue-Doku](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html))
3. **Neu: SSM-Parameter** `/training/participant/queue-url` mit der Queue-URL.
4. `cdk bootstrap` (einmalig), dann `cdk diff` **lesen** und erst dann `cdk deploy`.
5. Beweis: schickt mit `aws sqs send-message` eine Nachricht und lest sie mit `receive-message` wieder aus.

## Teil 3 — Erster Bedrock-Call (≈20 min)

1. Findet euer nutzbares Nova-Inference-Profile (der Filter ist wichtig — die ungefilterte Liste enthält auch Profile anderer Anbieter und `global.`-Varianten):

   ```bash
   aws bedrock list-inference-profiles --region eu-west-1 \
     --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `eu.amazon.nova`)].inferenceProfileId'
   ```

   Nehmt ein Nova-Micro- oder Nova-Lite-Profil (billiges Modell) für die ersten Gehversuche.

2. Schreibt ein kleines Skript `bedrock_hello.py` (boto3, [`converse`-API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)), das eine Frage stellt und **Antwort + Token-Verbrauch** (`usage` in der Response) ausgibt.
3. Die Modell-ID kommt per Env-Variable ins Skript — nicht hartcodiert (warum? → Theorie-Folie "Merksatz").

## Zusatzaufgabe (schnelle Teilnehmer)

Gebt dem `converse`-Call ein `system`-Prompt ("Antworte in einem Satz, auf Deutsch") und vergleicht den Token-Verbrauch mit/ohne. Wo würdet ihr System-Prompts im echten System versionieren?

## Abschluss

- `cdk destroy` **nicht** ausführen — der Stack wird morgen weiterverwendet.
- Wer AccessDenied-Fehler sammelt: notieren! Genau diese Fehler sind der Unterschied zwischen LocalStack und echtem AWS (Theorie 02).
