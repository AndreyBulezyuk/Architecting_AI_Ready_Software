# Lösung T2/04

```bash
uv sync
uv run pytest -v            # sync-Vertrag + kompletter Async-Job-Lifecycle (live)
uv run python cleanup.py    # Queue + Answers-Tabelle entfernen
```

Stolpersteine aus der Übung:

- **Reihenfolge beim Submit** ([jobs.py](jobs.py)): erst `pending` in DynamoDB, **dann** `send_message`. Umgekehrt kann der Worker den Job beantworten, bevor der `GET`-Endpoint ihn kennt — oder der Consumer bekommt 404 auf eine gültige job_id.
- **`status` ist ein reserviertes Wort** in DynamoDB-Update-Expressions → `ExpressionAttributeNames={"#s": "status"}`.
- **Header in Fehlerantworten** (Teil 2, Recherchefrage): FastAPI baut für eine `HTTPException` eine frische Response — Header, die ihr vorher auf dem injizierten `Response`-Objekt gesetzt habt, verfallen. `Retry-After` gehört als `headers=`-Argument in die Exception.
- **healthz-Test ohne Container-Stopp**: `monkeypatch.setattr` auf die `driver`-Funktion, die eine Exception wirft — Fehlerpfade simuliert man, man provoziert sie nicht.
- **Idempotenz-Zusatzfrage**: Submit-seitige Dedup (Frage-Hash als `job_id`) ist die billigste Variante, ändert aber die Semantik (gleiche Frage = gleicher Job, auch Tage später — Cache!). Worker-seitige Dedup entspricht dem Kapitel-04-Muster. "Gar nicht" ist vertretbar, wenn doppelte LLM-Calls billiger sind als die Komplexität — Hauptsache, die Entscheidung ist dokumentiert.
