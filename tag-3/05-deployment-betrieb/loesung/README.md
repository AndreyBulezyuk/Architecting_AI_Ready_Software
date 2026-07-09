# Lösung T3/05

```bash
uv sync
uv run pytest -v          # 5 Assertions: jede Stack-Erweiterung einzeln bewiesen
npx cdk synth Neo4j       # offline prüfbar
```

Drei Erweiterungen gegenüber der Demo, jede mit eigenem Assertions-Test:

- **Verschlüsseltes Volume** (`encrypted=True`) — Data-at-rest-Verschlüsselung, bewiesen durch `test_data_volume_is_encrypted`.
- **SSM Session Manager statt SSH** — eine Instance-Role mit `AmazonSSMManagedInstanceCore` erlaubt Admin-Zugriff **ohne** offenen Port 22 und ohne Key-Pair, das leaken könnte. Zwei Tests: die Rolle hat die Policy, und Port 22 ist **nicht** offen (negativer Beweis).
- **Zweiter SSM-Parameter** (`/training/neo4j/browser-url`) — beide Parameter existieren.

Stolpersteine:

- **Assertions gegen die echte Template-Struktur**: Die Managed-Policy-ARN steht im Template als `Fn::Join` — die Assertion muss auf die verschachtelte Struktur matchen (`Match.array_with` + `string_like_regexp`), nicht auf einen fertigen String. `npx cdk synth` einmal von Hand lesen, bevor man die Assertion schreibt.
- **Der Kostenschutz muss jede Erweiterung überleben**: `test_still_no_nat_gateway` läuft weiter mit — eine Erweiterung, die versehentlich ein NAT Gateway einführt, fällt sofort auf.
- **CDK + pyright strict**: `ServicePrincipal`/`Role` implementieren `IPrincipal`/`IRole` über jsii-Decorators, die pyright nicht auflöst — gezielte `# pyright: ignore[reportArgumentType]` mit Begründung, `cdk synth` beweist die Korrektheit.
- **Nicht deployen ohne Not**: Der Stack kostet pro Stunde. Diese Lösung wird per Assertion + `synth` verifiziert, nicht deployt.
