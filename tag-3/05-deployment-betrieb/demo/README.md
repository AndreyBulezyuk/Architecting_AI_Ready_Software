# Demo T3/05 — Neo4j auf EC2 als Infrastructure-as-Code

Ablauf (~15 min). **Dieses Kapitel deployt nichts** — es beweist den Stack per `cdk synth` + Assertions (kein Stundenpreis, kein AWS-Zugang nötig).

```bash
cd tag-3/05-deployment-betrieb/demo
uv sync
uv run pytest -v          # 6 Assertions beweisen die tragenden Eigenschaften
npx cdk synth Neo4j       # Python → CloudFormation (offline)
```

> ⚠️ **`npx cdk deploy Neo4j` kostet Geld pro Stunde** (t4g.small). Nur am Schulungstag deployen, am Ende `npx cdk destroy Neo4j`. Die Demo zeigt bewusst nur `synth` + Tests.

**Wichtige Punkte:**

- [stacks/neo4j_stack.py](stacks/neo4j_stack.py): derselbe Neo4j-Container wie im lokalen `docker-compose.yml` (Image `neo4j:5.26-community`), per User-Data auf einer EC2-Instanz gestartet — das "lokal = Cloud"-Prinzip aus Tag 1, jetzt als Deployment.
- **Kostenbewusst gebaut** (Kosten-Radar aus Tag 1/03): `t4g.small` (ARM, ~0,50 $/Tag), **`nat_gateways=0`** + Public Subnet (ein NAT Gateway würde mehr kosten als die Instanz — die klassische Falle), `delete_on_termination=True` auf dem Volume.
- **Sicherheit:** Bolt/Browser-Ports nur für die Teilnehmer-CIDR offen, **nie** `0.0.0.0/0` für eine Datenbank — ein Test beweist das explizit negativ.
- [tests/test_stack.py](tests/test_stack.py): Die eigentliche Lektion des Kapitels — `cdk synth` allein ist **kein Beweis**. Die Assertions (`Template.from_stack`) prüfen Instanztyp, kein NAT Gateway, CIDR-Beschränkung, Wegwerf-Volume und den SSM-Parameter. Genau das verlangt die Projekt-Regel für CDK.
- Läuft komplett offline: kein AWS-Aufruf, kein Deploy — deshalb im CI ausführbar.
