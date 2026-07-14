# Übung T3/05 — Den Deployment-Stack erweitern & beweisen

**Ziel:** Infrastruktur wie Anwendungscode behandeln — den Neo4j-Stack erweitern und **jede** Änderung per `aws_cdk.assertions` beweisen, ohne zu deployen.
**Zeit:** ~75 min. **Voraussetzung:** Demo T3/05 gesehen; Tag-1/03-CDK-Grundlagen präsent.

**Begriffe für diese Übung:**

- **Assertion (CDK)**: Ein Test, der das aus dem Stack **synthetisierte** CloudFormation-Template auf bestimmte Eigenschaften prüft (`Template.from_stack(...).has_resource_properties(...)`) — offline, ohne Deploy.
- **SSM Session Manager**: Admin-Zugriff auf eine EC2-Instanz über die AWS-API statt SSH — kein offener Port 22, kein Key-Pair.

## Teil 1 — Nachziehen (≈15 min)

Demo ausführen (`pytest`, `npx cdk synth Neo4j`). Lest das synthetisierte Template einmal von Hand (`cdk.out/Neo4j.template.json`): Wo genau steht der Instanztyp, wo die Security-Group-Regeln? Das braucht ihr, um eure eigenen Assertions zu schreiben.

## Teil 2 — Stack erweitern (≈40 min)

Nehmt den Demo-Stack als Vorlage und fügt **drei** Dinge hinzu — **jedes mit einem eigenen Assertions-Test**:

1. **Verschlüsseltes Volume**: EBS-Volume (Elastic Block Store, die Festplatte der EC2-Instanz) mit `encrypted=True`. Beweist per Assertion, dass `Encrypted: true` im Template steht.
2. **SSM Session Manager statt SSH**: Hängt der Instanz eine IAM-Role mit der Managed Policy `AmazonSSMManagedInstanceCore` an. Beweist (a) die Rolle hat die Policy und (b) **Port 22 ist nicht offen** (negativer Test — die Abwesenheit eines Fehlers beweisen).
3. **Zweiter SSM-Parameter**: `/training/neo4j/browser-url` mit der HTTP-URL. Beweist, dass beide Parameter existieren.

**Recherche:** Die Managed-Policy-ARN erscheint im Template nicht als fertiger String, sondern als `Fn::Join`. Wie matcht ihr darauf? ([CDK assertions Matchers](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/Match.html))

## Teil 3 — Der Kostenschutz muss überleben (≈15 min)

1. Übernehmt `test_no_nat_gateway_is_created` und `test_bolt_is_never_open_to_the_world` aus der Demo in eure Test-Suite.
2. Führt sie **nach** euren Erweiterungen erneut aus — bleiben sie grün? (Sie müssen: eine Erweiterung darf weder ein NAT Gateway noch eine `0.0.0.0/0`-Regel einführen.)
3. **Warum ist ein negativer Test hier so wertvoll?** Notiert eure Begründung in einem Satz. (Tipp: Was beweist `resource_count_is(..., 0)`, das ein positiver Test nicht kann?)

## Zusatzaufgabe (schnelle Teilnehmer)

Recherchiert den **AgentCore-Deploy** für euren T2/05-Agenten: Welches Werkzeug ([AgentCore CLI](https://github.com/aws/agentcore-cli)), welche Schritte (Container → ECR → Runtime)? Dokumentiert die Befehle — **ausführen müsst ihr nichts** (Preview-Status, Kosten). Warum ist "dokumentieren, nicht ausführen" hier die ehrliche Wahl?

## Abschlussfragen

1. `cdk synth` läuft ohne Fehler durch. Warum reicht das **nicht** als Beweis, dass euer Stack korrekt ist? Nennt ein konkretes Beispiel, das synth durchlässt, aber eine Assertion fängt.
2. Blick zurück auf die ganze Schulung: Nennt für jede der 6 AI-Ready-Eigenschaften (Tag 1/01) das Kapitel, in dem ihr sie gebaut habt.

## Hinweise

- **Nicht deployen** (Stundenpreis!) — diese Übung wird per Assertion + `synth` verifiziert.
- `JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1` unterdrückt die Node-Version-Warnung.
- Lösung in `loesung/` — erst nach eigenem Versuch.
