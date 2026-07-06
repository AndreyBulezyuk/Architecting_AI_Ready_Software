# Demo 03 — Erster CDK-Deploy

Läuft im Sandbox-Account (~15 min), während die Teilnehmer-Accounts hochkommen:

```bash
# 1. Wer bin ich, wo bin ich?
aws sts get-caller-identity
echo $AWS_PROFILE   # → training-Profil, eu-west-1

# 2. CDK-App ansehen: infrastructure/ ist ein normales uv-Projekt
cd infrastructure
uv sync
cat stacks/base_stack.py        # ~30 Zeilen Python …

# 3. … werden zu CloudFormation
npx cdk synth | head -40        # Template zeigen, L2-Mehrwert erklären

# 4. Einmalig pro Account+Region
npx cdk bootstrap

# 5. Deploy + Beweis
npx cdk deploy TrainingBase
aws s3 ls | grep trainingbase   # Bucket existiert
aws ssm get-parameter --name /training/base/data-bucket-name --query Parameter.Value

# 6. Ausblick Aufräumen (nicht ausführen): npx cdk destroy TrainingBase
```

**Wichtige Punkte:**

- `cdk diff` vor jedem echten Deploy — Review-Artefakt wie ein Code-Diff
- Tags (`project`, `owner`) kommen zentral aus `app.py` — Grundlage für Kosten-Auswertung an Tag 3
- Der `qualifier`/Bootstrap-Stack ist der einzige "magische" Teil — einmal zeigen, entzaubern
