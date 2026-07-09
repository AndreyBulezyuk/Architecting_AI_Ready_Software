# Lösung T3/04

```bash
uv sync
uv run python report.py   # Kosten-Report über einen gemischten Workload
uv run pytest -v          # 2 Live-Tests: Routing + Preisberechnung
```

Beispiel-Ausgabe (echte Bedrock-Zahlen, schwanken leicht):

```text
classify   [cheap ]  $0.000079
classify   [cheap ]  $0.000075
summarize  [cheap ]  $0.000094
draft      [STRONG]  $0.000780
```

Der Draft-Task auf dem starken Tier dominiert die Gesamtsumme — genau der Punkt: **eine** teure Aufgabe kann mehr kosten als drei billige zusammen.

Stolpersteine aus der Übung:

- **Router als Kostenhebel** ([report.py](report.py)): Das `ROUTES`-Dict ist die eine Stelle, an der die Tier-Entscheidung fällt — dieselbe Struktur wie der T2/01-Router, hier aber unter dem Kosten-Blickwinkel. Den Draft auf Haiku umzurouten spart ~90 % *dieser Zeile*, aber nur, wenn die Antwortqualität reicht (Ragas prüfen, nicht raten).
- **Caching lohnt sich nicht immer** (Teil 3): Bei genau einem Task gibt es einen Cache-Write (1,25×) und **keinen** Read — reiner Verlust. Erst ab mehreren Anfragen mit demselben Prefix innerhalb der TTL dreht sich das. Die Cache-Hit-Ratio muss über ~30 % liegen.
- **`inputTokens` ≠ Gesamtkosten**: Cache-Tokens werden getrennt gezählt; `cost.py` addiert alle vier Felder mit ihren eigenen Faktoren.
- **Budget-Action als harter Deckel** (Zusatz): Ein Budget-*Alarm* schickt nur eine Mail — eine Budget-*Action* hängt bei Überschreitung eine IAM-Deny-Policy an und stoppt neue `InvokeModel`-Calls tatsächlich. Das ist der einzige Weg zu einem echten Ausgaben-Stopp (AWS deckelt sonst nicht hart — der ehrliche Punkt aus Tag 1/03).
