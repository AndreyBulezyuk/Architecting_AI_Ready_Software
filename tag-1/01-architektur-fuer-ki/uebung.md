# Übung 01 — AI-Ready-Assessment einer Bestandsanwendung

**Ziel:** Die 6 AI-Ready-Qualitätsmerkmale aus der Theorie auf ein konkretes System anwenden und eine Ziel-Architektur skizzieren.
**Form:** 2er/3er-Gruppen, ~45 min. Kein Code — Papier, Whiteboard oder Markdown/Mermaid.

## Ausgangslage: "TravelMate" (fiktiv)

TravelMate ist ein Reiseportal eines Mittelständlers:

- **Monolith** (Python/Django) mit synchronen HTTP-Calls zwischen allen Modulen
- **Eine** PostgreSQL-Datenbank für alles: Buchungen, Nutzerkonten, Reiseberichte (als HTML-Blobs), Support-Tickets
- Nächtlicher Cron-Job baut CSV-Exporte für das BI-Team
- Suchfunktion: SQL `LIKE`-Queries über Reisebericht-Titel
- Neu vom Management gewünscht:
  1. **Persönliche Reiseempfehlungen** ("Kunden wie du buchten…") — aktuell hart codierte Top-10-Liste
  2. **Frage-Antwort-Assistent** über 40.000 Reiseberichte und interne Richtlinien
  3. **Automatische Ticket-Zusammenfassung** für den Support

Ein erster Prototyp des Assistenten existiert: Ein Entwickler ruft **synchron im Request-Handler** die OpenAI-API auf, hängt die letzten 5 Suchtreffer der `LIKE`-Query als Kontext an und gibt die Antwort ungeprüft als HTML aus. Bei Lastspitzen laufen Requests in Timeouts; die API-Rechnung im letzten Monat war eine Überraschung.

## Aufgabe

### Teil 1 — Assessment (Tabelle ausfüllen)

Bewertet TravelMate je Merkmal mit ⛔ (fehlt), 🟡 (Ansätze), ✅ (vorhanden) und begründet in einem Satz:

| Merkmal | Bewertung | Begründung |
|---|---|---|
| Ereignisorientiert | | |
| Daten-zugänglich | | |
| Kontext-fähig | | |
| Nichtdeterminismus-fest | | |
| Beobachtbar | | |
| Modell-austauschbar | | |

### Teil 2 — Ziel-Architektur skizzieren

Zeichnet ein Mermaid-`flowchart` (max. 20 Nodes) für die drei gewünschten KI-Features. Beantwortet dabei:

1. Welche der drei Features müssen **asynchron** laufen, welche dürfen synchron bleiben — und warum?
2. Welche **Datenablagen** braucht ihr zusätzlich zur bestehenden PostgreSQL (Vektor? Graph? Key-Value?) und wofür genau?
3. An welchen Stellen platziert ihr **Validierung/Guardrails**, bevor LLM-Output Nutzer erreicht?

### Teil 3 — Abgrenzung (Diskussion, 3 Sätze)

Der CTO fragt: *"Brauchen wir dafür jetzt ein Data-Science-Team und SageMaker?"* — Formuliert eine Antwort mit der Abgrenzung aus der Theorie.

### Zusatzfrage (für schnelle Gruppen)

Das BI-Team will die Empfehlungsqualität "irgendwie messen". Welche Kennzahlen würdet ihr ab Tag 1 mitloggen, damit spätere Evaluation (Tag 3) möglich wird?

## Hilfsmittel

- Theorie-Folien dieses Kapitels ([theorie.md](theorie.md))
- [Mermaid Flowchart-Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [AWS Prescriptive Guidance: Event-driven architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/pub-sub.html)
