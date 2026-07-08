# Demo 02 — Stack starten & Smoke-Tests

Ablauf (~15 min), alles live im Terminal:

```bash
# 1. Im Repo-Root: Stack starten und Health beobachten
docker compose --profile emulation up -d   # Neo4j + LocalStack (Profil nur für dieses Kapitel)
docker compose ps          # warten bis alles "healthy"

# 2. Kurz zeigen: Neo4j Browser http://localhost:7474 (neo4j/trainingpass)

# 3. In dieses Demo-Projekt wechseln und Tests laufen lassen
cd tag-1/02-setup-lokal/demo
uv sync                    # legt .venv an, installiert gepinnte Dependencies
uv run pytest -v           # 3 Tests: Neo4j erreichbar, Neo4j Vector Index, LocalStack-S3

# 4. Qualitäts-Tooling einmal zeigen
uv run ruff check .
uv run pyright
```

**Wichtige Punkte:**

- `config.py`: alle Endpoints/Credentials kommen aus einer Settings-Klasse ([pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)) mit Env-Override — dieselbe Klasse zeigt später auf AWS statt LocalStack.
- Der S3-Test nutzt **normales boto3** — nur `endpoint_url` unterscheidet lokal von AWS.
- Smoke-Tests als Muster: jedes weitere Kapitel-Projekt beginnt mit einem Test, der die Umgebung beweist.
