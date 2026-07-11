---
theme: default
title: "T2/05 — Agenten & Orchestrierung"
info: "Tag 2, Kapitel 5 · Architecting AI-Ready Applications"
transition: fade
mdc: false
---

# Agenten & Orchestrierung

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

Das Modell entscheidet, welche Tools es braucht — Strands Agents + MCP

**Tag 2 · Kapitel 05**

<!--
Tag 2 · Kapitel 05 · Folie 1/7 (Titel)

Bogen des Tages schließen: T2/01 Output-Verträge, T2/02-03 Retrieval, T2/04 Service — jetzt dreht sich die Kontrolle um: Bisher rief UNSER Code das LLM; ab jetzt entscheidet das LLM, welchen Code es ruft.
-->

---

# Was ein Agent ist — und was nicht

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

```mermaid
flowchart LR
    U[Frage] --> L[LLM\nplant nächsten Schritt]
    L -->|Tool-Call| T1[search_travel_reports]
    L -->|Tool-Call| T2[Neo4j via MCP]
    T1 --> L
    T2 --> L
    L -->|genug Kontext| A[Antwort]
    style L fill:#e9f7ef,stroke:#27ae60
```

- **Agent = Modell + Tools + System-Prompt in einer Schleife**: Das LLM entscheidet pro Runde, ob es ein Tool ruft oder antwortet ([Strands: model-driven](https://strandsagents.com/docs/))
- Der Unterschied zu T2/01–04: Dort war der Ablauf **fest programmiert** (erst Retrieval, dann Antwort) — hier wählt das Modell den Ablauf selbst
- Kein Agent nötig, wenn der Ablauf immer gleich ist! RAG-Pipeline (T2/02) bleibt die richtige Wahl für "Frage rein → Antwort raus" — Agenten lohnen sich bei **variablen** Wegen

<!--
Tag 2 · Kapitel 05 · Folie 2/7 (Was ein Agent ist)

Anti-Hype-Punkt zuerst: Die RAG-Baseline aus T2/02 ist KEIN Agent und soll auch keiner werden. Agent-Overhead (mehr Calls, weniger Determinismus) muss durch variable Aufgabenwege gerechtfertigt sein.
-->

---

# Strands Agents: Agent in wenigen Zeilen

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

```python
from strands import Agent, tool
from strands.models import BedrockModel

@tool
def search_travel_reports(question: str) -> str:
    """Semantische Suche in den TravelMate-Reiseberichten."""   # der Docstring
    return format_hits(search(question, k=3))                    # IST die Tool-Doku!

agent = Agent(
    model=BedrockModel(boto_session=session, model_id=MODEL_ID, temperature=0.0),
    tools=[search_travel_reports],
    system_prompt=SYSTEM_PROMPT_V1,
)
result = agent("Wohin für eine Hüttentour?")
result.metrics.tool_metrics       # welche Tools liefen — beweisbar, testbar!
```

- [Strands](https://strandsagents.com/docs/) ist model-driven: keine Graphen verdrahten, das Modell führt die Schleife — [AWS-eigenes SDK](https://github.com/strands-agents/harness-sdk), produktiv u. a. in Amazon Q Developer
- **Docstring + Typen = Tool-Vertrag**: Davon hängt ab, ob das Modell das Tool richtig benutzt — Tool-Beschreibungen sind Prompt-Engineering

<!--
Tag 2 · Kapitel 05 · Folie 3/7 (Strands)

Live-Vergleich zu LangGraph ziehen: Strands = Modell entscheidet; LangGraph = expliziter Graph, wenn deterministische Kontrolle Pflicht ist. Beide legitim — Auswahlkriterium ist, wer den Kontrollfluss besitzen soll.
-->

---

# MCP in einer Minute (nicht Kursthema, aber gut zu kennen)

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

**[MCP](https://modelcontextprotocol.io/)** (Model Context Protocol): offener Standard, wie ein LLM Werkzeuge und Daten *entdeckt und nutzt* — wie USB-C für KI-Tools.

- **MCP-Server** = stellt **Tools** (Aktionen) und **Resources** (lesbare Daten) bereit
- **MCP-Client** = die Seite am Agenten, die den Server einbindet (Strands, Claude Desktop, IDE …)

| Use Case | Client | Server | Nutzen |
|---|---|---|---|
| DB-Zugriff für Agenten | Agent (Strands) | Neo4j-MCP-Server | Agent schreibt Cypher selbst — keine Query von Hand als Tool |
| Interne API für KI öffnen | Chat-Assistent | eigener MCP-Server um die API | **einmal** bauen, jeder MCP-Client nutzt ihn |
| Dev-Tools in der IDE | IDE (z. B. Cursor) | GitHub-/Filesystem-Server | Standard statt proprietärem Plugin je Tool |

<!--
Tag 2 · Kapitel 05 · Folie 4/7 (MCP in einer Minute)

MCP steht nicht in der offiziellen Agenda — deshalb bewusst NUR diese eine Begriffs-Folie plus die Praxis-Folie danach, keine Vertiefung. Kernbild: USB-C für KI-Tools. Client = Agent-Seite, Server = Tool-Anbieter-Seite. Die Tabelle zeigt, WANN sich ein eigener Server lohnt: wenn mehrere Clients dasselbe System brauchen.
-->

---

# Ein eigener MCP-Server: einmal bauen, überall nutzen

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

```mermaid
flowchart LR
    A[Euer Agent] -->|MCP| S[Eigener MCP-Server]
    C[Claude Desktop] -->|MCP| S
    I[IDE] -->|MCP| S
    S --> SYS[(Interne API /\nDatenbank)]
    style S fill:#e9f7ef,stroke:#27ae60
```

```python
neo4j_mcp = MCPClient(lambda: stdio_client(StdioServerParameters(
    command="uvx", args=["mcp-neo4j-cypher"], env={...})))
with neo4j_mcp:                                    # Session offen halten!
    agent = Agent(model=model, tools=[*own_tools, *neo4j_mcp.list_tools_sync()])
```

- **Ein Server, viele Clients** — den [offiziellen Neo4j-MCP-Server](https://neo4j.com/docs/mcp/current/) nutzt der Agent in der Übung, ohne eine Zeile Cypher vorzugeben
- Grenze ehrlich benannt: MCP-Tools sind so sicher wie ihr Server — dem Agenten **nur Lese-Zugänge** geben; Schreibrechte sind eine Architektur-Entscheidung, kein Default

<!--
Tag 2 · Kapitel 05 · Folie 5/7 (Eigener MCP-Server)

Der Aha-Moment der Übung: Niemand hat dem Agenten Cypher beigebracht — er holt das Schema über den MCP-Server und formuliert die Query selbst. Danach sofort die Sicherheitsfrage: Wer will das mit Schreibrechten in Produktion? (Niemand → read-only Neo4j-User.)
-->

---

# Orchestrierung: Ein Agent, viele Agenten, oder ein Workflow?

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

| Muster | Wann | Beispiel |
|---|---|---|
| **Fester Ablauf** (kein Agent) | Weg ist immer gleich | RAG-Pipeline T2/02 |
| **Single Agent + Tools** | variable Wege, EIN Verantwortungsbereich | unsere Demo |
| **Multi-Agent** (Agent als Tool) | klar trennbare Spezialgebiete | Recherche- + Buchungs-Agent |
| **Workflow-Engine** ([Step Functions](https://docs.aws.amazon.com/step-functions/)) | Determinismus/Audit Pflicht | Genehmigungsprozesse |

- **Agenda-Frage "Service-Mesh vs. Orchestrierungs-Framework":** Das Mesh (Netzwerk-Ebene: Routing, mTLS, Retries) bleibt zuständig — Agent-Orchestrierung ist **Anwendungs-Ebene**. Kein Entweder-oder, verschiedene Schichten
- Betriebskosten steigen mit jeder Agenten-Runde (jeder Schritt = LLM-Call) — `metrics.accumulated_usage` im Blick behalten; Deployment: Tag 3 (AgentCore)

<!--
Tag 2 · Kapitel 05 · Folie 6/7 (Orchestrierung)

Die Mesh-Frage kommt aus der offiziellen Agenda — Antwort: unterschiedliche Schichten. Istio sieht HTTP-Calls zwischen Services; wer welchen Agenten-Schritt WARUM macht, ist Anwendungslogik. Beides existiert parallel.
-->

---

# Demo & Übung

###### tag-2/05-agenten-orchestrierung · Tag 2 · Kapitel 05

**Demo:** Agent mit zwei Python-Tools über den Reiseberichten — `result.metrics` beweist, welches Tool das Modell wann gewählt hat.

**Übung:**

1. Eigenes Tool schreiben (Docstring = Vertrag!) und erleben, wie die Tool-Beschreibung die Modell-Wahl steuert
2. **MCP:** offiziellen Neo4j-Server anbinden — der Agent beantwortet Struktur-Fragen mit selbst geschriebenem Cypher
3. Zusatz: Agent-as-Tool (ein Spezialist als Werkzeug eines Generalisten)

**Kosten:** Jede Agenten-Runde ist ein LLM-Call — die Übung bleibt im Centbereich, aber der Multiplikator ist der Punkt.

<!--
Tag 2 · Kapitel 05 · Folie 7/7 (Demo & Übung)

Tagesabschluss nach der Übung: Die komplette T2-Kette einmal durchzeigen — Output-Vertrag → Embeddings → GraphRAG → Service → Agent. Morgen wird genau diese Kette beobachtbar, evaluierbar und deploybar gemacht.
-->
