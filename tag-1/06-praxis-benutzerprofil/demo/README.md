# Demo 06 — Referenz-Komponente im Schnelldurchlauf

> **Status: Konzept** — der Demo-Code entsteht nach Review des Kapitel-Zuschnitts (siehe `.claude/TODOs.md`).

Geplanter Ablauf (~15 min): Die fertige Referenz-Implementierung der Benutzerprofil-Komponente wird einmal komplett durchgespielt — danach bauen die Teilnehmer sie in Etappen selbst (`uebung.md`).

## 1. Kaltstart zeigen

```bash
cd tag-1/06-praxis-benutzerprofil/demo
uv sync
uv run python seed_catalog.py        # ~20 Reiseangebote mit Embeddings (Kap.-05-Store)
uv run fastapi dev api.py            # GET /user_profiles/user-42 → 404, noch kein Profil
```

## 2. Events erzeugen und Pipeline laufen lassen

```bash
uv run python simulate_user.py user-42   # publiziert 5 Such-/Buchungs-Events (Kap. 04)
uv run python worker.py                   # konsumiert Events → Roh-Signale → Schwelle erreicht
                                          # → Bedrock-Verdichtung → Profil + Embedding + Empfehlungen
```

## 3. Ergebnis ansehen und diskutieren

- `GET /user_profiles/user-42` → jetzt 200 mit `interests`, `persona_summary`, `recommendations`
- In Postgres zeigen: Roh-Signale vs. materialisiertes Profil (zwei Tabellen, eine Wahrheit)
- Noch einmal 5 Events → Profil ändert sich **erst nach erneuter Verdichtung** (eventual consistency live erlebt)

**Wichtige Punkte:**

- Der GET-Pfad bleibt auch bei ausgefallenem Bedrock funktionsfähig — er liest nur die Tabelle (Resilienz-Argument).
- Der LLM-Schritt läuft mit `BEDROCK_MODEL_ID` aus der Umgebung (Kap.-03-Merksatz) und validiert die Antwort gegen das Pydantic-Schema; eine kaputte Antwort wird einmal wiederholt, dann verworfen und geloggt.
- Kostenblick: 5 Events = **eine** Verdichtung, nicht 5 LLM-Calls.
