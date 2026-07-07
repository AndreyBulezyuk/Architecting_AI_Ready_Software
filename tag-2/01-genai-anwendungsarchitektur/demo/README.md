# Demo T2/01 — Converse-Basics & strukturierte Outputs

Ablauf (~15 min), gegen echtes Bedrock (AWS-Profil aktiv, Kosten: Bruchteile eines Cents):

```bash
cd tag-2/01-genai-anwendungsarchitektur/demo
uv sync

# 1. Basis-Call mit Usage-Tracking
uv run python chat.py "Was ist ein Event-Bus?"

# 2. Strukturierte Extraktion — erzwungener Tool-Call
uv run python structured.py "Max, 34, aus Berlin, wandert und taucht gern."

# 3. Beides als Tests
uv run pytest -v
```

**Wichtige Punkte:**

- [config.py](config.py): Modell-ID ist Config mit verifiziertem Default; der `aws login`-Provider braucht `botocore[crt]` (steht in `pyproject.toml` — die Lehre aus Kapitel 03).
- [chat.py](chat.py): jede Response liefert `usage` — wird ab jetzt immer mitgenommen (Tag-3-FinOps beginnt hier).
- [structured.py](structured.py): `toolChoice` **zwingt** das Modell in das Pydantic-Schema (`model_json_schema()`); validiert wird trotzdem, mit genau einem Retry samt Fehlertext im Prompt.
- Live zeigen: `stopReason` der Response ist `tool_use`, und das Ergebnis steckt im `toolUse.input`-Block — nicht im Text.
