# Übung T2/01 — Model-Router mit Kosten-Messung & eigener Output-Vertrag

**Ziel:** Modellwahl und Output-Verträge als Architektur-Entscheidungen umsetzen: ein Router wählt das Modell nach Aufgabentyp, jeder Call wird gemessen, und euer eigenes Schema wird per erzwungenem Tool-Call bedient.
**Zeit:** ~75 min. **Voraussetzung:** Demo T2/01 gesehen, AWS-Profil aktiv, Bedrock Model Access.

## Teil 1 — Nachziehen (≈10 min)

Demo ausführen (`chat.py`, `structured.py`, `pytest`). Schaut euch in `structured.py` an, wo das `toolUse.input` aus der Response gefischt wird — das braucht ihr gleich.

## Teil 2 — Model-Router (≈30 min)

1. Findet per CLI eure aktiven Claude-Profile (Filter aus Übung 03!) und wählt ein **billiges** (Haiku) und ein **starkes** (Sonnet/Opus) Profil.
2. Baut `router.py`: ein `TaskType` (`Literal["classify", "summarize", "draft"]`) wird über ein Konfigurations-Dict auf eine Modell-ID gemappt; `run_task(task_type, text)` führt den Call aus und gibt Antwort **plus Messwerte** zurück: Modell-ID, Input-/Output-Tokens, Latenz in ms.
3. Lasst dieselbe Zusammenfassungs-Aufgabe einmal über das billige und einmal über das starke Modell laufen und vergleicht Tokens, Latenz und Qualität. Überrascht euch das Ergebnis?

**Recherche:** [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) — rechnet für euren Vergleich die ungefähren Kosten pro Call aus (Preise als Konstanten in eurem Code, mit Quellen-Kommentar und Datum!).

## Teil 3 — Eigener Output-Vertrag (≈30 min)

TravelMate-Support bekommt Freitext-Nachrichten. Baut die Extraktion:

1. Pydantic-Modell `SupportTicket`: `category: Literal["buchung", "zahlung", "beschwerde", "sonstiges"]`, `priority: Literal["niedrig", "normal", "hoch"]`, `summary: str` (max. 200 Zeichen — wie erzwingt Pydantic das?).
2. `extract_ticket(text)` mit **erzwungenem Tool-Call** (Muster aus der Demo), Validierung und genau einem Retry.
3. Testet mit drei Nachrichten: eine eindeutige Beschwerde, eine Zahlungsfrage — und ein Text, der **gar kein** Support-Anliegen ist ("Wie wird das Wetter morgen?"). Was macht euer Vertrag im dritten Fall, und ist das das richtige Verhalten? (Tipp: Braucht das Schema eine Kategorie mehr?)

## Zusatzaufgabe (schnelle Teilnehmer)

Chat-UX: baut `ask_streaming()` mit [`converse_stream`](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html) und gebt die Tokens fortlaufend auf stdout aus. Wo kommen in einem Stream die `usage`-Daten her?

## Abschlussfragen

1. Nach welchen Kriterien außer Kosten würdet ihr das Routing entscheiden — und wer im Team pflegt die Routing-Tabelle?
2. Warum validieren wir trotz erzwungenem Schema noch mit Pydantic? Nennt zwei konkrete Fälle, die `toolChoice` **nicht** verhindert.

## Hinweise

- Ausschließlich `eu.`-Inference-Profile verwenden; Modell-IDs als Config.
- Lösung in `loesung/` — erst nach eigenem Versuch.
