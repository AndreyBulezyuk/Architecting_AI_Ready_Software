# Trainer-Runbook 03 — AWS live vorbereiten

Die Teilnehmer-E-Mails liegen erst am Schulungstag vor → Account-Erstellung passiert **live** (Schritt 2, läuft parallel zur Theorie). Alles davor ist **einmalige Vorbereitung vor der Schulung**.

## A. Vorbereitung (Wochen vorher, einmalig)

- [ ] **Account-Quota erhöhen**: AWS Organizations erlaubt per Default nur ~10 Accounts. Service Quotas → *AWS Organizations* → *Default maximum number of accounts* auf ≥ Teilnehmerzahl + 5 erhöhen. **Vorlauf mehrere Tage!**
- [ ] Organization mit OU `Training` anlegen:

  ```bash
  ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
  aws organizations create-organizational-unit --parent-id "$ROOT_ID" --name Training
  ```

- [ ] **SCP** auf die OU: nur `eu-west-1` + globale Services erlauben, teure Instanztypen verbieten (Vorlage: [AWS-Doku "Deny region access"](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples_general.html)).
- [ ] **IAM Identity Center** aktivieren (Region `eu-west-1`), Permission Set `TrainingAdmin` (Managed Policy `AdministratorAccess` — die Isolation leistet der Account, nicht die Policy; SCPs begrenzen von außen).
- [ ] Im **eigenen** Sandbox-Account: kompletten Tag-1-Ablauf einmal durchspielen (bootstrap → deploy → Bedrock-Call). Bedrock **Model Access** für Claude-Modelle testen.
- [ ] E-Mail-Schema festlegen: jeder Org-Account braucht eine **einzigartige** Mail. Plus-Adressierung nutzen: `trainer+tn01@firma.de`, `trainer+tn02@firma.de`, … landen alle im Trainer-Postfach.

## B. Live in der Schulung (~30 min, parallel zur Theorie 03)

**1. Teilnehmerliste erfassen** (Name + E-Mail für Identity Center; die Account-Mail ist die Plus-Adresse des Trainers).

**2. Accounts erstellen** (je ~2–5 min, asynchron — früh starten):

```bash
for i in 01 02 03; do
  aws organizations create-account \
    --email "trainer+tn${i}@firma.de" \
    --account-name "training-tn-${i}" \
    --iam-user-access-to-billing DENY
done
aws organizations list-create-account-status \
  --states IN_PROGRESS FAILED   # beobachten bis alles SUCCEEDED
```

**3. Accounts in die OU verschieben** (damit SCPs greifen):

```bash
aws organizations move-account --account-id <ID> \
  --source-parent-id "$ROOT_ID" --destination-parent-id <OU_ID>
```

**4. Identity-Center-Zugänge**: pro Teilnehmer User anlegen (echte Teilnehmer-Mail) und dem Account mit `TrainingAdmin` zuweisen. Teilnehmer bekommen sofort die Einladungs-Mail → können parallel Passwort/MFA setzen.

**5. Budget pro Account** (über die Org-Zugriffsrolle in jeden Account):

```bash
# pro Account: Rolle annehmen und 20-EUR-Budget mit 80%-Alarm anlegen
aws sts assume-role --role-arn arn:aws:iam::<ACCOUNT_ID>:role/OrganizationAccountAccessRole \
  --role-session-name budget-setup
# dann: aws budgets create-budget ... (Vorlage in scripts/, siehe TODO)
```

**6. Bedrock Model Access**: machen die Teilnehmer selbst in ihrer Console (Bedrock → *Model access* → Anthropic-Modelle anfordern; i. d. R. sofort aktiv). Einzige Console-Ausnahme der Schulung — kein stabiles API verfügbar.

## C. Stolperfallen & Fallback

- Account-Erstellung schlägt fehl → meist Quota (siehe A) oder Mail bereits verwendet.
- **Fallback**, wenn Organizations klemmt: ein gemeinsamer Sandbox-Account, pro Teilnehmer ein Identity-Center-User + eigener Ressourcen-Prefix. Verliert Kosten-Isolation, rettet aber den Tag.
- Teilnehmer ohne MFA-Gerät: TOTP-App reicht (kein Hardware-Key nötig).

## D. Kosten-Radar (was kann Geld kosten?)

Alles, was die Schulung standardmäßig nutzt, ist **nutzungsbasiert** und bleibt pro Teilnehmer für 3 Tage im einstelligen Euro-Bereich:

| Service | Kostenmodell | Einschätzung 3 Tage |
|---|---|---|
| Bedrock (Claude on-demand, Embeddings) | pro Token, kein Leerlaufpreis | größter Posten, grob 1–3 € bei Haiku-Default |
| DynamoDB (on-demand), SQS, SNS, EventBridge, S3, SSM, Lambda | pro Request/GB | Centbeträge |
| CloudWatch Logs | pro GB ingestiert | Centbeträge |

> ## ⚠️ ACHTUNG: Ressourcen mit STUNDENPREIS — nach dem Schulungstag ZWINGEND zerstören
>
> - **EC2-Instanz für Neo4j** (Tag 2/3, `t4g.small` ≈ 0,02 $/h ≈ 0,50 $/Tag): läuft **24/7 weiter**, auch nachts. Am Ende jedes Schulungstags: `cdk destroy` bzw. Instanz stoppen; nach der Schulung Accounts schließen.
> - **Niemals anlegen** (Kostenfallen, teils >10 $/Tag pro Stück, ohne dass man etwas tut):
>   - **OpenSearch Serverless** — Standard-Vektorstore von Bedrock Knowledge Bases! OCU-Grundlast läuft stündlich auch im Leerlauf. Genau deshalb nutzen wir KB **nicht**.
>   - **Neptune / Neptune Analytics** (Grundlage des Bedrock-KB-GraphRAG-Features)
>   - **Bedrock Provisioned Throughput** (Model Units kosten dreistellig pro Tag!) — wir bleiben on-demand
>   - **NAT Gateway** (entsteht schnell versehentlich bei eigenen VPCs — Default-VPC nutzen)
>   - **Aurora/RDS-Cluster**, SageMaker-Endpoints, ECS/Fargate-Dauerdienste
> - Schutznetz: SCP gegen teure Instanztypen (Abschnitt A), 20-€-Budget-Alarm pro Account (Abschnitt B5), am letzten Tag gemeinsames `cdk destroy` als Übungsabschluss.

## E. Nach der Schulung (Aufräumen)

```bash
aws organizations close-account --account-id <ID>
```

- **Limit beachten:** AWS erlaubt nur ~10 % der Accounts pro 30 Tage zu schließen — bei vielen Teilnehmern gestaffelt schließen oder Accounts für die nächste Schulung recyceln (dann: [aws-nuke](https://github.com/ekristen/aws-nuke) zum Leerräumen).
- Identity-Center-User und Plus-Mail-Zuordnung dokumentiert ablegen.
