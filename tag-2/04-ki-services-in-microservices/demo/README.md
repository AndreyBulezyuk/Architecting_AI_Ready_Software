# Demo T2/04 — Der Assistant-Service

Ablauf (~15 min): Neo4j läuft, AWS-Profil aktiv.

```bash
cd tag-2/04-ki-services-in-microservices/demo
uv sync
uv run pytest -v                  # Vertrag, healthz, Validierung, Throttling→503 + MCP-Tools
uv run fastapi dev service.py     # dann http://localhost:8000/docs öffnen
```

Live in den `/docs` (Swagger UI) zeigen:

1. `POST /v1/ask` mit einer echten Frage → Antwort mit `sources`, Tokens, Latenz
2. Dieselbe Frage nochmal mit `"question": "hi"` → 422 (der Vertrag schützt auch vor Kosten)
3. `GET /healthz` → 200, und erklären, warum hier **kein** Bedrock-Call steckt

**MCP-Server (Brücke zu Kapitel 05):**

```bash
uv run python mcp_server.py       # startet den MCP-Server (stdio)
```

Dasselbe `rag.py` als MCP — ein Tool `ask_travelmate` für Agenten, ein `search_travel_reports` für Rohsuche. Die Demo zeigt: **ein Austauschpunkt, zwei Schnittstellen** (REST für HTTP-Konsumenten, MCP für Agenten/IDEs). Den Server mit Claude Desktop, Cursor oder dem Strands-Agenten aus Kapitel 05 verbinden.

**Wichtige Punkte:**

- [rag.py](rag.py) ist der **Austauschpunkt**: GraphRAG aus T2/03 könnte die Baseline hier ersetzen, ohne dass sich am Service etwas ändert — genau dafür kapseln wir.
- [service.py](service.py): Throttling wird zu **503 + `Retry-After`** (Header gehören in die `HTTPException` — auf dem `Response`-Objekt gehen sie bei Fehlern verloren); `refused` ist **200**, kein Fehler.
- [mcp_server.py](mcp_server.py): dieselbe `rag.py`-Funktion, anderes Protokoll — der Referenzpunkt dafür, warum MCP kein Ersatz für REST ist, sondern eine **Ergänzung** für tool-orientierte Konsumenten (Agenten, IDEs). Die 3 Offline-Tests in `test_mcp_server.py` prüfen Tool-Discovery und Schemas ohne AWS — zeigen, wie man MCP-Server testet.
- Der Throttling-Test braucht kein echtes Throttling: `monkeypatch` ersetzt `rag.answer` — Fehlerpfade müssen testbar sein, ohne den Fehler zu provozieren.
- Die eine `print`-Zeile pro Request (request_id, Modell, Tokens, Latenz) ist der Rohstoff für Tag 3 — aus ihr wird morgen ein OTel-Span.
