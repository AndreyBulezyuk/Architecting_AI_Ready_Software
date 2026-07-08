# Lösung T2/05

```bash
uv sync
uv run pytest -v                 # eigener Tool-Mix + MCP-Cypher, live (~30 s)
uv run python mcp_agent.py       # "Wie viele Chunks pro Reiseziel?" — Agent schreibt das Cypher
```

Stolpersteine aus der Übung:

- **MCP-Session offen halten** ([mcp_agent.py](mcp_agent.py)): Die MCP-Tools leben nur innerhalb `with mcp_client:` — Agent **im** Kontextmanager bauen und aufrufen. Außerhalb schlagen die Tool-Calls fehl, weil der Server-Subprozess weg ist.
- **Docstring-Experiment (Teil 2.3):** Ohne aussagekräftigen Docstring wählt das Modell das Tool selten oder falsch — die Beschreibung ist die einzige Information, die das Modell über eure Funktion hat.
- **Sicherheits-Check (Teil 3.3):** Zwei Ebenen — (1) Neo4j-Benutzer mit reinen Leserechten für den MCP-Server, (2) beim Agent-Bau nur die Lese-Tools aus `list_tools_sync()` durchreichen (Filter nach Tool-Namen). Verlasst euch nie allein auf den System-Prompt ("nutze nur lesende Queries") — der ist eine Bitte, keine Berechtigung.
- **Env-Variablen für den Subprozess:** `uvx` braucht ein `PATH` im `env`-Dict, sonst startet der Server auf manchen Systemen nicht; Verbindungsdaten (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`) kommen aus den Settings, nie hartcodiert.
- **Agent-as-Tool (Zusatz):** Jede Delegation kostet einen zusätzlichen LLM-Call des äußeren Agenten — der Multiplikator aus der Theorie-Folie 5 in Aktion.
