# Lösung 06

Die Referenzlösung ist bewusst identisch mit der [Demo](../demo/) — dort steht die komplette, getestete Implementierung aller vier Etappen (`infra.py`, `worker.py`, `condense.py`, `catalog.py`, `api.py` + End-to-End-Test). Nach der Übung dort vergleichen.

Stolpersteine je Etappe:

- **A (Dedup):** `put_item` mit `ConditionExpression="attribute_not_exists(signal_id)"` — atomar, kein `get_item`-Race. Das Duplikat wirft `ConditionalCheckFailedException`, die ihr fangt und zählt.
- **B (404):** "Kein Profil" ist ein Fakt, den der Aufrufer sehen muss — ein leeres 200 verschleiert den Zustand und bricht Caching-/Retry-Logik der Konsumenten.
- **C (Verdichtung):** `temperature=0` + `maxTokens`-Deckel für deterministisch-knappe Antworten; validiert wird trotzdem (`model_validate_json` + genau 1 Retry mit Fehlertext). Schwelle prüfen **nach** dem Signal-Write, Signale nach der Verdichtung als `condensed` markieren — sonst verdichtet jedes weitere Event erneut.
- **D (Empfehlungen):** Katalog und Interessen **müssen** durch dieselbe Embedding-Funktion laufen — zwei verschiedene Funktionen erzeugen inkompatible Vektorräume, die Suche liefert dann plausiblen Zufall.
- **Aufräumen:** `uv run python cleanup.py` in der Demo entfernt Bus, Rule, Queues und beide Tabellen.
