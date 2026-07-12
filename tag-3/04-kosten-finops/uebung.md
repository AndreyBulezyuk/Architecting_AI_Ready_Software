# Übung T3/04 — Kosten-Report für einen Workload

**Ziel:** Aus diffusem "LLMs kosten Geld" einen konkreten Report machen — pro Aufgabe das Modell wählen, `usage` messen, USD ausrechnen, und den Effekt von Caching und Tier-Wahl über den ganzen Mix beziffern.
**Zeit:** ~75 min. **Voraussetzung:** Demo T3/04 gesehen; AWS-Profil aktiv.

**Begriffe für diese Übung:**

- **Cache-Hit-Ratio**: Anteil der Anfragen, die einen bereits gecachten Prefix wiederverwenden. Unter ~30 % kostet Caching mehr, als es spart (die 1,25×-Writes überwiegen).
- **Cost Allocation Tag**: ein Tag (`project`, `owner`, …) auf AWS-Ressourcen, mit dem sich Kosten pro Team/Feature auswerten lassen.

## Teil 1 — Nachziehen (≈15 min)

Demo ausführen (`caching.py`, `tiering.py`, `pytest`). Notiert die zwei Kernzahlen (Cache-Read-Anteil, Pro/Lite-Faktor) — die braucht ihr als Vergleich für euren eigenen Report.

## Teil 2 — Der Kosten-Report (≈35 min)

Baut `cost_report(workload)` (Vorlage: `cost.py` aus der Demo für die USD-Rechnung):

1. Ein `workload` ist eine Liste von `(task_type, text)` — mindestens `classify`, `summarize`, `draft`. Routet jeden Task über ein Dict auf einen Tier (billig für classify/summarize, stark für draft — Router aus T2/01).
2. Pro Task: `converse` aufrufen, `usage` auslesen, mit `cost.py` in USD umrechnen. Der Report gibt pro Zeile Task, Modell und Kosten aus, plus eine Gesamtsumme.
3. Lasst denselben Workload **einmal komplett auf dem billigen Tier** laufen (auch den Draft) und vergleicht die Gesamtsumme. Wie viel spart das Tiering — und würdet ihr den Draft-Task wirklich auf Nova Lite umstellen? (Schaut euch die **Antwortqualität** an, nicht nur den Preis — Rückgriff auf Ragas, Tag 3/02.)

## Teil 3 — Caching über den Workload (≈25 min)

1. Erweitert euren Report so, dass ein großer **gemeinsamer System-Prompt** (z. B. eine Wissensbasis) mit `cachePoint` an jeden Call gehängt wird.
2. Messt die Gesamtkosten des Workloads **mit** und **ohne** Cache-Point. Ab welcher Workload-Größe lohnt sich das Caching — und was passiert bei nur **einem** einzigen Task (Cache-Write ohne Read)?
3. **Recherche:** Berechnet für euren Workload die tatsächliche Cache-Hit-Ratio und vergleicht sie mit dem ~30-%-Breakeven aus der Theorie. Liegt ihr drüber oder drunter?

## Zusatzaufgabe (schnelle Teilnehmer)

Skizziert eine **Budget-Action**, die bei Überschreitung wirklich stoppt (nicht nur alarmiert): [AWS Budgets Actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html) kann eine IAM-Policy anhängen, die `bedrock:InvokeModel` verweigert. Warum ist das ein **harter** Deckel, den ein bloßer Budget-Alarm nicht bietet?

## Abschlussfragen

1. Ihr habt jetzt drei Hebel: Caching, Tiering, Batch. Ordnet jeden einem konkreten Teil eurer TravelMate-Anwendung zu (Chat-Assistent, Nightly-Re-Embedding, Support-Klassifikation) — welcher Hebel passt wo, und warum nicht überall alle drei?
2. Ein Kollege will "zur Sicherheit immer das stärkste Modell" nehmen. Formuliert die Gegenposition in zwei Sätzen — mit Bezug auf Tag 3/02 (Evaluation).

## Hinweise

- Preise in `cost.py` sind Beispielwerte — vor echten Kostenaussagen gegen die [Pricing-Seite](https://aws.amazon.com/bedrock/pricing/) prüfen.
- Lösung in `loesung/` — erst nach eigenem Versuch.
