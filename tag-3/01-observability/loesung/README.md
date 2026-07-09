# Lösung T3/01

```bash
uv sync
uv run pytest -v   # live: Bedrock + Neo4j + Langfuse, ~10 s
```

```python
# Konsole zum Ausprobieren:
from traced_assistant import ask
ask("Wohin für eine anstrengende Hüttentour?", session_id="sess-1")
ask("Und was, wenn ich lieber baden will?", session_id="sess-1")  # gleiche Session!
```

Danach in Langfuse (<http://localhost:3000>) im Tab **Sessions** nachschauen — beide Traces hängen an `sess-1`.

Stolpersteine aus der Übung:

- **Framework-Instrumentierung zuerst prüfen, dann selbst instrumentieren** (Kernlektion des Kapitels): [assistant.py](assistant.py) ist **unverändert** aus T2/05 kopiert — kein einziger manueller Span. `invoke_agent Strands Agents` (AGENT), `execute_event_loop_cycle` (SPAN), `search_travel_reports`/`list_destinations` (TOOL) und `chat` (GENERATION, inkl. korrektem Bedrock-Modellnamen) kommen alle aus Strands selbst.
- **Die eine Lücke:** Strands weiß nichts von "mehreren zusammengehörigen Anfragen" — dafür braucht es [traced_assistant.py](traced_assistant.py)s Wrapper-Span mit `session.id`. Der Wrapper wird zum Trace-**Root**; Strands' eigene Spans hängen sich als Kinder darunter — reine OTel-Context-Propagation, kein Sonderfall.
- **Eigene Tools bekommen denselben TOOL-Span automatisch** (Teil 3) — der `@tool`-Decorator selbst löst die Instrumentierung aus, nicht ob das Tool aus Strands oder von euch stammt.
- **`StrandsTelemetry()` nur einmal aufrufen** ([tracing.py](tracing.py)): Der Modul-Import-Zeitpunkt sorgt dafür, dass der Exporter genau einmal registriert wird, auch wenn `traced_assistant` mehrfach importiert wird.
