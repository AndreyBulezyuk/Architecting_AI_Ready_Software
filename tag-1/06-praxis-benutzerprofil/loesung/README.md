# Lösung 06

Vollständige Lösung der vier Etappen, mit eigenen Ressourcen-Namen (`t06-ueb-…`, Neo4j-Label `UebOffer`), damit nichts mit der Demo kollidiert. Voraussetzungen: AWS-Profil aktiv, Bedrock Model Access, Neo4j läuft.

```bash
uv sync
uv run pytest -v            # Etappen A -> B -> C/D als Tests (~40 s, 1 Bedrock-Call)
uv run fastapi dev api.py   # die gestufte Lese-API von Hand erkunden
uv run python cleanup.py    # Bus, Rule, Queues, Tabellen entfernen
```

**Der wichtigste Unterschied zur Demo:** [api.py](api.py) ist **gestuft** wie die Übung. Etappe B verlangt eine Antwort aus den **Roh-Signalen** (`signal_count`, `last_seen_at`, `interests: []`), lange bevor ein LLM je gelaufen ist — erst nach der Summarization (C/D) füllt derselbe Endpoint `interests`, `persona_summary`, `travel_style` und `recommendations` dazu. Die Demo-API kennt nur den Endzustand.

Stolpersteine je Etappe:

- **A (Dedup):** `put_item` mit `ConditionExpression="attribute_not_exists(signal_id)"` — die Prüfung passiert atomar im Schreib-Call selbst. Die naive Alternative (erst per `get_item` prüfen, dann schreiben) hätte eine **Race Condition**: Zwischen Prüfen und Schreiben kann ein parallel laufender Worker dasselbe Signal einfügen — beide sehen "existiert nicht" und schreiben doppelt. Das Duplikat wirft stattdessen `ConditionalCheckFailedException`; der Test beweist: 6 Events ⇒ genau 5 Items.
- **B (404):** 404 heißt "wir kennen diesen Nutzer gar nicht" — das muss vom Fall "Nutzer bekannt, aber noch keine Summarization gelaufen" (200 mit leeren `interests`) unterscheidbar bleiben. Ein leeres 200 für Unbekannte verschleiert den Zustand.
- **C (Summarization):** `temperature=0` + `maxTokens`-Deckel; validiert wird trotzdem (`model_validate_json` + 1 Retry). **LLM-JSON-Falle:** Claude wickelt das JSON gern in einen ```json-Fence — bei `temperature=0` deterministisch, der Retry allein rettet nichts. Deshalb `_strip_code_fence` in [summarize.py](summarize.py) vor der Validierung.
- **D (Empfehlungen):** Katalog und Interessen laufen durch **dieselbe** Embedding-Funktion — zwei verschiedene Funktionen erzeugen inkompatible Vektorräume. Pro Label+Property nur ein Vector Index → eigenes Label `UebOffer` mit eigenem Index.
