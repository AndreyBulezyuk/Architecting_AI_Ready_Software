# Lösung T2/01

```bash
uv sync
uv run pytest -v          # 4 Live-Tests (Haiku + Sonnet, wenige Cent-Bruchteile)
uv run python router.py   # Vergleich billig vs. stark auf derselben Aufgabe
```

Stolpersteine aus der Übung:

- **`summary: str = Field(max_length=200)`** — Pydantic erzwingt die Länge; ohne Validierung würde ein zu langer LLM-Text still durchrutschen (Abschlussfrage 2, Fall 1; Fall 2: `toolChoice` verhindert keine inhaltlich falschen, aber schema-gültigen Werte).
- **Off-Topic-Fall (Teil 3):** Ohne eine Kategorie `kein_anliegen` presst das erzwungene Schema *jeden* Text in eine Support-Kategorie — der Vertrag muss den "trifft nicht zu"-Fall selbst abbilden. Der Test beweist das Verhalten.
- **Preise als Konstanten** in [config.py](config.py) sind Beispielwerte mit Quellen-Kommentar — vor jeder Schulung gegen die [Pricing-Seite](https://aws.amazon.com/bedrock/pricing/) prüfen.
- Latenz misst ihr selbst (`time.perf_counter`) — die Response enthält keine Ende-zu-Ende-Latenz.
