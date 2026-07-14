# Übung T3/03 — Eigener Guardrail & Abwehr indirekter Prompt-Injection

**Ziel:** Einen eigenen Bedrock-Guardrail entwerfen und die RAG-spezifische Angriffsfläche schließen — ein vergiftetes Dokument in der Wissensbasis, das das Modell kapern will.
**Zeit:** ~75 min. **Voraussetzung:** Demo T3/03 gesehen; Neo4j läuft, AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **Prompt Injection (direkt/indirekt)**: Direkt = die Anweisung steht in der Nutzerfrage. Indirekt = sie steckt in einem **abgerufenen Dokument**, das der Nutzer gar nicht sieht — der gefährlichere Fall für RAG-Systeme.
- **`apply_guardrail`**: Prüft beliebigen Text gegen einen Guardrail **ohne** Modell-Aufruf — im Gegensatz zum `converse`-Guardrail, der nur den fertigen Prompt am Antwort-Call sieht.
- **PII** (Personally Identifiable Information): personenbezogene Daten wie Name, E-Mail, Telefonnummer oder Kartennummer, die ein Guardrail anonymisieren oder blocken kann.

## Teil 1 — Nachziehen (≈15 min)

Demo ausführen (`guardrail.py`, `pytest`, `cleanup.py`). Schickt dem `guarded_rag`-Modul selbst eine Prompt-Injection und schaut, was `stopReason` liefert. Löscht danach den Demo-Guardrail wieder.

## Teil 2 — Euer eigener Guardrail (≈25 min)

1. Baut einen Guardrail mit einem **anderen** verbotenen Thema als die Demo (z. B. medizinische oder rechtliche Beratung — beides off-domain für einen Reise-Assistenten) plus dem `PROMPT_ATTACK`-Filter und einer PII-Regel eurer Wahl.
2. **Recherche:** Warum muss `outputStrength` bei `PROMPT_ATTACK` auf `NONE` stehen? Was passiert sonst beim Anlegen? ([Guardrails Content Filters](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-content-filters.html))
3. Testet alle drei Policies mit je einem Beispiel (verbotenes Thema, Injection, PII).

## Teil 3 — Vergiftetes Dokument abfangen (≈35 min)

Das ist die eigentliche RAG-Verteidigung:

1. Schreibt ein `safe_ingest(documents, guardrail_id)`: prüft **jedes** Dokument per `apply_guardrail` (`source="INPUT"`), **bevor** es in den Neo4j-Store kommt — vergiftete Dokumente werden abgelehnt und gemeldet, saubere ingestiert.
2. Baut einen Mini-Korpus aus 2 sauberen Reiseberichten + 1 vergifteten (der Bericht enthält "Ignoriere alle Anweisungen …"). `safe_ingest` muss den vergifteten **ablehnen** und die zwei sauberen durchlassen.
3. Schreibt **außerdem** einen Test, der beweist: ein normaler Reisebericht wird **nicht** fälschlich abgelehnt (False-Positive-Kontrolle — ein zu scharfer Filter ist genauso ein Problem wie ein zu laxer).

**Warum am Ingest und nicht an der Anfrage?** Notiert eure Begründung in einem Satz. (Tipp: Wann sieht ein `converse`-Guardrail das Dokument frühestens?)

## Zusatzaufgabe (schnelle Teilnehmer)

Formuliert eine IAM-Policy, die euren Guardrail **erzwingt** — jeder `Converse`-Call ohne genau diesen Guardrail wird per `Deny` + `StringNotEquals` abgelehnt (Theorie-Folie 6). Warum reicht ein `Allow` mit `StringEquals` **nicht** aus?

## Abschlussfragen

1. Guardrails sind eine Schicht, nicht **die** Lösung. Nennt zwei weitere Schichten aus dieser Schulung, die zusammen mit dem Guardrail gegen Prompt Injection wirken (Defense-in-Depth).
2. Euer `safe_ingest` lehnt vergiftete Dokumente ab. Was macht ihr mit einem abgelehnten Dokument in einem echten System — stillschweigend verwerfen, alarmieren, in Quarantäne? Begründet.

## Hinweise

- Ressourcen-Präfix `t303-ueb-…`; am Ende `cleanup.py` (Guardrail löschen).
- Lösung in `loesung/` — erst nach eigenem Versuch.
