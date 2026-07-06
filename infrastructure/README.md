# infrastructure/ — AWS CDK App

Zentrale CDK-App der Schulung; Stacks wachsen kapitelweise. Eigenes uv-Projekt, CDK-CLI kommt aus dem Root-`package.json`.

```bash
uv sync

# Install aws cli
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws login --profile ai-training

npx cdk synth            # offline: Python → CloudFormation
npx cdk bootstrap        # 1x pro Account+Region (Teilnehmer: Übung 03)
npx cdk deploy TrainingBase
npx cdk ls          list all stacks in the app
npx cdk deploy      deploy this stack to your default AWS account/region
npx cdk diff        compare deployed stack with current state
npx cdk docs        open CDK documentation
```

| Stack | Kapitel | Inhalt |
|---|---|---|
| `TrainingBase` (`stacks/base_stack.py`) | tag-1/03 | S3-Bucket + SSM-Parameter — beweist die Toolchain |

Konventionen: alle Ressourcen mit `RemovalPolicy.DESTROY` (Wegwerf-Accounts), Tags `project`/`owner` zentral in `app.py`, Region kommt aus dem AWS-Profil (`eu-west-1`).
