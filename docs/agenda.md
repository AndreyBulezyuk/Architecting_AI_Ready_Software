# Offizielle Seminar-Agenda (Referenz)

Quelle: [Architecting AI-Ready Applications – Softwarearchitektur für KI-Systeme](https://www.it-schulungen.com/seminare/kuenstliche-intelligenz/ki-coding-ki-softwareentwicklung/architecting-ai-ready-applications-softwarearchitektur-fuer-ki-systeme.html) (identisches Seminar auf expertes.de), 3 Tage.

## Lernziele

Nach Abschluss können die Teilnehmer:

- Event-getriebene Architekturen für KI-Workloads konzipieren
- RAG-Muster für Unternehmensanwendungen integrieren (in diesem Repo: **GraphRAG**)
- Daten-zentrierte Microservices für KI-Modelle gestalten
- Observability für KI-Komponenten definieren
- Domänenmodelle mit KI-Komponenten verbinden
- Kosten- und Sicherheitsaspekte berücksichtigen

## Zielgruppe

Softwarearchitekten, Systemarchitekten, Lead-/Senior-Entwickler, Tech Leads, Principal Engineers, technisch orientierte IT-Verantwortliche.

## Voraussetzungen

- Erfahrung mit Softwarearchitektur (Microservices, verteilte Systeme)
- Grundverständnis Domain-Driven Design
- Vertrautheit mit Cloud-Plattformen (hier: AWS)
- Programmierkenntnisse (hier: Python)

## Module → Tagesordner

| Offizielles Modul | Inhalt | Repo |
|---|---|---|
| Modul 1: Event-Driven & Daten-zentrierte Grundlagen | Rolle der Architektur in KI-Systemen (Abgrenzung Data Science/MLOps), Event-Driven Architecture für KI-Workloads, daten-zentrierte Architekturen & Persistenzkonzepte, Praxisbeispiel Benutzerprofil-Komponente für KI-Personalisierung | `tag-1/` |
| Modul 2: RAG-Muster und KI-zentrierte Services | Architektur von GenAI-Anwendungen, RAG-Patterns (Dokumentenpipeline, Embeddings, Indizes, Query-Flows) — hier als GraphRAG, KI-Services in Microservice-Landschaften, Orchestrierung von KI-Funktionen und Agenten | `tag-2/` |
| Modul 3: Production-Readiness, Sicherheit & Kosten | Observability für KI-Komponenten, Qualitäts- und Sicherheitsanforderungen, Kostenaspekte & FinOps, Deployment- und Betriebsmodelle | `tag-3/` |

**Bewusste Abweichung:** Statt klassischem Vector-only-RAG setzen wir GraphRAG (Neo4j + Vector Index) ein — bessere Generierungsqualität bei Multi-Hop-Fragen und expliziten Beziehungen. Vector-RAG wird als Baseline in Tag 2 trotzdem kurz gebaut, damit der Qualitätsunterschied messbar wird (Ragas-Vergleich in Tag 3).
