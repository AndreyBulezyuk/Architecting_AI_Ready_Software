# Demo 06 — Referenz-Komponente im Schnelldurchlauf

Ablauf (~15 min): Die fertige Referenz-Implementierung der Benutzerprofil-Komponente wird einmal komplett durchgespielt — danach bauen die Teilnehmer sie in Etappen selbst (`uebung.md`). Voraussetzungen: AWS-Profil aktiv, Bedrock Model Access, Neo4j läuft (`docker compose up -d`).

## 1. Kaltstart zeigen

```bash
cd tag-1/06-praxis-benutzerprofil/demo
uv sync
uv run python infra.py               # Bus, Rule, Queue+DLQ, zwei DynamoDB-Tabellen
uv run python catalog.py             # 20 Reiseangebote mit Embeddings nach Neo4j
uv run fastapi dev api.py            # GET /user_profiles/user-42 → 404, noch kein Profil
```

## 2. Events erzeugen und Pipeline laufen lassen

```bash
uv run python simulate_user.py user-42   # 6 Events (5 unique + 1 Duplikat) auf den Bus
uv run python worker.py                   # konsumiert → dedupliziert → Schwelle erreicht
                                          # → Bedrock-Verdichtung → Profil + Empfehlungen
```

## 3. Ergebnis ansehen und diskutieren

- `GET /user_profiles/user-42` → jetzt 200 mit `interests`, `persona_summary`, `travel_style`, `recommendations`
- In DynamoDB zeigen: `t06-profile-signals` (Roh-Signale) vs. `t06-user-profiles` (materialisierte Sicht) — zwei Tabellen, eine Wahrheit
- Im Neo4j Browser: `MATCH (o:Offer) RETURN o` — der Katalog, aus dem die Empfehlungen kommen
- Noch einmal 5 Events → Profil ändert sich **erst nach erneuter Verdichtung** (eventual consistency live erlebt)

**Wichtige Punkte:**

- Der GET-Pfad liest nur DynamoDB — er bleibt auch bei ausgefallenem Bedrock funktionsfähig (Resilienz-Argument).
- 6 Events = **eine** Verdichtung, nicht 6 LLM-Calls; das Duplikat scheitert am `ConditionExpression`-Muster aus Kapitel 04.
- Die LLM-Antwort wird gegen `ProfileSummary` (Pydantic) validiert, ein Retry mit Fehlerhinweis, dann Fehlerpfad — der Vertrag aus Kapitel 03, an Tag 2 kommt die robustere Tool-Call-Variante.
- Empfehlungen nutzen **dieselbe** Embedding-Funktion wie der Katalog (Kapitel-05-Regel) — heute fake, morgen Bedrock.
- Aufräumen: `uv run python cleanup.py` (alles nutzungsbasiert, aber Wegwerf-Design gilt).
