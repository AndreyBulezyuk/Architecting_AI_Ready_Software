# Demo T3/01 — Der T2/04-Service wird beobachtbar

Ablauf (~15 min): Neo4j läuft, AWS-Profil aktiv, Langfuse läuft (`docker compose --profile observability up -d`, dauert beim ersten Start ~1 min).

```bash
cd tag-3/01-observability/demo
uv sync
uv run pytest -v                # 2 Tests: liest die Traces über die Langfuse-API zurück
uv run fastapi dev service.py   # dann eine echte Frage gegen /v1/ask schicken
```

Danach live in Langfuse zeigen: <http://localhost:3000> (Login `trainer@example.com` / `trainingpass`, per Headless-Init aus der Compose-Datei vorbereitet) → **Traces** → `rag.answer` öffnen.

**Wichtige Punkte:**

- [tracing.py](tracing.py): ein `Tracer`, der direkt auf Langfuses OTLP-Endpoint (`/api/public/otel/v1/traces`) zeigt — kein Sidecar, kein Collector nötig für die Schulung.
- [rag.py](rag.py): **ein** Root-Span (`rag.answer`) pro Anfrage, **ein** Child-Span (`vector_search`) für die Retrieval-Stufe — die Trace-Baum-Struktur bildet exakt den Ablauf aus T2/02 ab.
- Die Attribut-Namen sind [OTel-GenAI-Konventionen](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (`gen_ai.request.model`, `gen_ai.usage.*`) — Langfuse übersetzt sie **automatisch** in Modell, Tokens und sogar **Kosten** (Theorie-Folie 4, live im UI zeigen: die Kostenspalte ist gefüllt, ohne dass wir eine Preistabelle gepflegt haben).
- Der `print`-Zeile aus T2/04 ist komplett verschwunden — die Trace **ist** jetzt das Log.
- [langfuse_api.py](langfuse_api.py): Die Tests lesen die eigene Trace über die Langfuse-API zurück.
