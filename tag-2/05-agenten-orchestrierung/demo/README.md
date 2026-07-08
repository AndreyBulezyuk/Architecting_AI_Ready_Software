# Demo T2/05 — Ein Agent, der selbst entscheidet

Ablauf (~15 min): Neo4j läuft, AWS-Profil aktiv.

```bash
cd tag-2/05-agenten-orchestrierung/demo
uv sync
uv run pytest -v                                        # beweist Tool-Nutzung per metrics
uv run python assistant.py "Wohin für eine Hüttentour?" # Antwort + tools used + Tokens
uv run python assistant.py "Zu welchen Zielen habt ihr Berichte?"
```

**Wichtige Punkte:**

- [assistant.py](assistant.py): Agent = Modell + Tools + System-Prompt — keine Schleife, kein Graph im eigenen Code; die Schleife führt [Strands](https://strandsagents.com/docs/).
- Die **zwei Fragen wählen verschiedene Tools** — live zeigen, dass `tools used` sich unterscheidet, ohne dass irgendwo ein `if` steht.
- Docstring + Typen der `@tool`-Funktionen sind der Vertrag fürs Modell — Tool-Beschreibungen sind Prompt-Engineering (Experiment dazu in der Übung).
- `result.metrics.tool_metrics` und `accumulated_usage`: Tool-Einsatz und Token-Verbrauch sind **messbar** — so testen wir Agenten, statt Verhalten zu vermuten.
- System-Prompt-Regel "nur Fakten aus den Tools" + ehrliches Scheitern — dieselbe Disziplin wie in T2/02, nur dass jetzt das Modell den Weg wählt.
