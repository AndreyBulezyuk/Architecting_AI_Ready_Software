# Demo T3/02 — Die T2/02-Baseline mit Ragas bewerten

Ablauf (~15 min): Neo4j läuft, AWS-Profil aktiv.

```bash
cd tag-3/02-evaluation-qualitaet/demo
uv sync
uv run pytest -v          # ~45 s, 3 Fragen × 3 Metriken über Bedrock
uv run python evaluate.py # dieselbe Auswertung, lesbar auf der Konsole
```

**Wichtige Punkte:**

- [ragas_bedrock.py](ragas_bedrock.py) ist der aufwendigste Teil des Kapitels: Ragas hat **keinen** eigenen Bedrock-Adapter, sondern nutzt die [`instructor`](https://python.useinstructor.com/)-Bibliothek für strukturierte Outputs. Zwei Stolpersteine, nur durch echte Aufrufe gefunden (nicht aus der Doku ablesbar): der Judge-Client muss **async** sein (`instructor.from_bedrock(..., async_client=True)`), und Ragas' Standardparameter schicken `temperature` **und** `top_p` gleichzeitig — Bedrocks Converse-API lehnt das für Claude ab, also wird `top_p` nach dem Bauen aus den `model_args` gelöscht.
- **Versions-Falle:** `ragas>=0.4.3` bricht mit dem aktuellsten `langchain-community` (entfernter Importpfad, [offener Ragas-Bug #2745](https://github.com/vibrantlabsai/ragas/issues/2745)) — deshalb `langchain-community<0.4` in der `pyproject.toml`, mit Kommentar und Link.
- [eval_dataset.py](eval_dataset.py): Frage + **Referenzantwort von Hand** — das ist exakt der "Fragenkatalog mit erwarteter Antwort", den T2/02 und T2/03 schon als Übungsergebnis verlangt haben.
- [evaluate.py](evaluate.py): pro Frage läuft die **echte** T2/02-Baseline (Retrieval + Bedrock-Antwort), danach bewerten drei [Ragas-Metriken](https://docs.ragas.io/en/stable/concepts/metrics/) dasselbe Ergebnis aus verschiedenen Blickwinkeln:
  - **Faithfulness**: Behauptet die Antwort etwas, das der Kontext nicht hergibt? (Live-Beispiel: eine erfundene Antwort bekommt hier 0.0, die echte Baseline meist 0.8–1.0)
  - **Context Precision**: Ist der gefundene Kontext überhaupt relevant für die Referenzantwort?
  - **Context Recall**: Deckt der gefundene Kontext die Referenzantwort **vollständig** ab?
- Die Scores schwanken leicht zwischen Läufen (LLM-as-Judge ist selbst ein LLM-Aufruf) — das ist normal, kein Bug. Deshalb prüft der Test einen **Schwellwert**, keinen exakten Wert.
