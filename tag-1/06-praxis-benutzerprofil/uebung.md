# Übung 06 — Benutzerprofil-Komponente bauen (Tagesabschluss)

**Ziel:** Eine event-getriebene Benutzerprofil-Komponente mit KI-Personalisierung — das Praxisbeispiel der Agenda, zusammengesetzt aus allem, was heute gebaut wurde.
**Zeit:** Rest des Tages (~2,5 h). **Team:** einzeln oder 2er-Teams.
**Etappen A + B sind Pflicht; C + D nach Fortschritt.** Jede Etappe hat ein klares "Fertig"-Kriterium.

## Ausgangslage

- AWS-Profil aktiv, Bedrock Model Access vorhanden (Kapitel 03); Neo4j läuft (`docker compose up -d`).
- Ihr dürft euren Code aus den Übungen 04/05 wiederverwenden — genau dafür war er da.

## Etappe A — Event-Ingest & Roh-Signale (~40 min)

1. EventBridge-Rule + Queue `t06-<name>-profile-events` (+ DLQ) + Worker (idempotent! Dedup-Muster aus Übung 04).
2. Der Worker schreibt pro Event ein Item in eine DynamoDB-Tabelle `profile_signals` (Partition Key `user_id`, Sort Key `signal_id` = `event_id`) — dazu `kind` (`SearchSubmitted`/`BookingCreated`), `payload`, `occurred_at` und ein Flag `summarized=false`.
3. Producer-Skript `simulate_user.py`: publiziert für eine `user_id` 5 gemischte Events (nutzt eure Modelle `SearchSubmitted`/`BookingCreated` aus Übung 04).

**Fertig, wenn:** ein pytest beweist: 6 publizierte Events (davon 1 Duplikat) ⇒ genau 5 Items in `profile_signals`. (Wie erzwingt DynamoDB die Dedup ohne vorheriges `get_item`? → `ConditionExpression`.)

## Etappe B — Lese-API (~30 min)

1. FastAPI-App mit `GET /user_profiles/{user_id}` ([FastAPI-Tutorial](https://fastapi.tiangolo.com/tutorial/first-steps/)).
2. Response ist ein Pydantic-Modell: vorerst `user_id`, `signal_count`, `last_seen_at` (per `query` aus `profile_signals` aggregiert), `interests: []` leer.
3. Unbekannte `user_id` ⇒ `404` (nicht `200` mit leerem Profil — warum? Notiert eure Begründung).

**Fertig, wenn:** `uv run fastapi dev` läuft und ein pytest mit [`TestClient`](https://fastapi.tiangolo.com/tutorial/testing/) 200- und 404-Fall abdeckt. **Kein LLM-Call in diesem Pfad.**

## Etappe C — LLM-Summarization (~45 min)

**Begriff:** *Summarization* = das LLM fasst viele Roh-Signale (Suchtexte, Buchungen) zu einem strukturierten, validierten Profil zusammen — der etablierte Fachbegriff für diesen Schritt.

1. Pydantic-Schema `ProfileSummary` (`interests: list[str]` max. 5, `persona_summary: str` max. 2 Sätze, `travel_style: Literal["budget","comfort","luxury","unknown"]`).
2. Funktion `summarize_profile(user_id)`: liest alle Signale, baut einen Prompt ("Antworte NUR mit JSON nach diesem Schema …"), ruft Bedrock `converse` auf (Muster aus Übung 03, Modell-ID aus der Env) und validiert mit `model_validate_json`.
3. Ungültiges JSON ⇒ **ein** Retry mit Fehlerhinweis im Prompt, danach aufgeben und loggen. **Bekannte Falle:** Das LLM wickelt das JSON gern in einen ```json-Code-Fence — den müsst ihr vor `model_validate_json` entfernen; bei `temperature=0` kommt im Retry deterministisch dieselbe Antwort, der Retry allein rettet euch also nicht.
4. Der Worker aus Etappe A stößt die Summarization an, sobald ein Nutzer ≥ 5 Signale ohne `summarized`-Flag hat; Ergebnis landet in einer DynamoDB-Tabelle `user_profiles` (`user_id`, `interests`, `persona_summary`, `travel_style`, `updated_at`), die Signale werden als `summarized=true` markiert. Die API liefert das Profil aus.

**Fertig, wenn:** `simulate_user.py` + Worker-Lauf ⇒ `GET /user_profiles/{id}` zeigt echte, vom LLM extrahierte Interessen.
**Recherche:** Wie erzwingt man knappe, deterministische Antworten? (`temperature`, `maxTokens` in [`inferenceConfig`](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-parameters.html))

## Etappe D — Embedding & Empfehlungen (~30 min)

1. Seed-Skript legt ~20 Reiseangebote als `:Offer`-Knoten in Neo4j an (Beschreibungstext, embedded, eigener Vector Index — Kapitel-05-Muster).
2. Nach jeder Summarization: `interests` als Text embedden (Fake-Embedding aus Kapitel 05 — **gleiche Funktion wie der Katalog!**) und Top-3-Angebote per `db.index.vector.queryNodes` ins Profil-Item materialisieren (`recommendations`).
3. API-Response um `recommendations` erweitern.

**Fertig, wenn:** Ein Nutzer, der nur nach Strand sucht, bekommt erkennbar Strand-Angebote — und die API bleibt schnell, weil alles vorberechnet ist (kein LLM, kein Embedding im GET-Pfad).

## Abschlussrunde (Plenum)

- Zeigt euer Profil-JSON. Welche Etappe hat am meisten Zeit gekostet — und war es die, die ihr erwartet hättet?
- Wo würde diese Komponente in eurer echten Systemlandschaft stehen, und wer wären ihre Konsumenten?
- Ausblick Tag 2: Der Chat-Assistent wird dieses Profil als **Kontext** nutzen — Personalisierung ohne zusätzliches Training.
