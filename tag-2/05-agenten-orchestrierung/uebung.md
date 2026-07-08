# Übung T2/05 — Eigene Tools & Datenbank-Zugriff via MCP

**Ziel:** Erleben, dass Tool-Beschreibungen Prompt-Engineering sind — und dem Agenten per MCP echten Datenbank-Zugriff geben, ohne eine Zeile Cypher vorzugeben.
**Zeit:** ~75 min. **Voraussetzung:** Demo T2/05 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **Tool**: Eine Python-Funktion, die das Modell aufrufen darf. Docstring + Parameter-Typen sind der Vertrag, nach dem das Modell entscheidet, **ob und wie** es sie nutzt.
- **MCP (Model Context Protocol)**: Offener Standard, über den Tool-Server ihre Fähigkeiten beschreiben — ein MCP-Server (z. B. der offizielle von Neo4j) funktioniert mit jedem MCP-fähigen Agenten, egal welches Framework.

## Teil 1 — Nachziehen (≈15 min)

Demo-Tests + `uv run python assistant.py` ausführen. Schaut euch `result.metrics.tool_metrics` an: Welches Tool lief bei welcher Frage — und stimmt das mit eurer Erwartung überein?

## Teil 2 — Euer eigenes Tool (≈25 min)

1. Schreibt ein Tool `current_season(month: int) -> str` (Monat → Jahreszeit, reine Python-Funktion) und gebt es dem Agenten dazu.
2. Stellt eine Frage, die **beide** Tools braucht ("Es ist Monat 12 — welche Jahreszeit, und welcher Bericht passt dazu?"). Beweist per `tool_metrics`, dass beide liefen.
3. **Experiment:** Löscht den Docstring eures Tools (bzw. ersetzt ihn durch "Hilfsfunktion") und stellt dieselbe Frage. Was passiert — und warum? (Antwort in einem Satz notieren.)

## Teil 3 — MCP: Der Agent schreibt sein eigenes Cypher (≈30 min)

1. Bindet den [offiziellen Neo4j-MCP-Server](https://neo4j.com/docs/mcp/current/) als Subprozess an (`uvx mcp-neo4j-cypher`, Verbindungsdaten als Env-Variablen — Muster in der Lösung erst nach eigenem Versuch!). **Recherche:** Wie kommen MCP-Tools in einen Strands-Agenten, und warum muss die MCP-Session während des Agent-Laufs offen bleiben? ([Strands MCP-Doku](https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/))
2. Fragt: *"Wie viele T4Chunk-Knoten gibt es pro doc_id?"* — ohne dass ihr irgendwo Cypher geschrieben habt. Prüft in `tool_metrics`, welche MCP-Tools der Agent benutzt hat.
3. Sicherheits-Check: Welche Tools bietet der Server außer Lesen an — und wie verhindert ihr in Produktion, dass ein Agent schreibt? (Mindestens zwei Ebenen: Neo4j-Benutzerrechte und Tool-Auswahl beim Agent-Bau.)

## Zusatzaufgabe (schnelle Teilnehmer)

Agent-as-Tool: Verpackt euren Demo-Agenten als `@tool` eines zweiten Agenten ("Concierge"), der zusätzlich `current_season` besitzt. Wann lohnt diese Aufteilung — und was kostet sie pro Frage zusätzlich?

## Abschlussfragen

1. Für welche zwei Aufgaben aus eurem Arbeitsalltag wäre ein Agent gerechtfertigt — und für welche zwei ausdrücklich nicht (fester Ablauf reicht)?
2. Der Agent ruft euren T2/04-Service morgen als Tool auf. Was muss am Service-Vertrag **nicht** geändert werden — und warum war das Absicht?

## Hinweise

- `temperature=0.0` fürs Testen; `callback_handler=None` hält stdout sauber.
- Der erste `uvx mcp-neo4j-cypher`-Start lädt das Paket herunter (~1 min) — einmalig.
- Lösung in `loesung/` — erst nach eigenem Versuch.
