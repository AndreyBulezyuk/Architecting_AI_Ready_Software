# Übung 06 — Benutzerprofil-Komponente bauen (Tagesabschluss)

> **Status: Konzept** — Feinschliff und `loesung/` folgen nach Review (siehe `.claude/TODOs.md`).

**Ziel:** Eine event-getriebene Benutzerprofil-Komponente mit KI-Personalisierung — das Praxisbeispiel der Agenda, zusammengesetzt aus allem, was heute gebaut wurde.
**Zeit:** Rest des Tages (~2,5 h). **Team:** einzeln oder 2er-Teams.
**Etappen A + B sind Pflicht; C + D nach Fortschritt.** Jede Etappe hat ein klares "Fertig"-Kriterium.

## Ausgangslage

- Lokaler Stack läuft (`docker compose up -d`), AWS-Profil aktiv, Bedrock Model Access vorhanden (Kapitel 03).
- Ihr dürft euren Code aus den Übungen 04/05 wiederverwenden — genau dafür war er da.

## Etappe A — Event-Ingest & Roh-Signale (~40 min)

1. Queue `t06-profile-events` + Worker (idempotent! Dedup-Muster aus Übung 04).
2. Der Worker schreibt pro Event eine Zeile in eine Tabelle `profile_signals(user_id, kind, payload, occurred_at)` — `kind` ist `search` oder `booking`.
3. Producer-Skript `simulate_user.py`: publiziert für eine `user_id` 5 gemischte Events (nutzt eure Modelle `SearchSubmitted`/`BookingCreated` aus Übung 04).

**Fertig, wenn:** ein pytest beweist: 5 publizierte Events (davon 1 Duplikat) ⇒ genau 4 Zeilen in `profile_signals`.

## Etappe B — Lese-API (~30 min)

1. FastAPI-App mit `GET /user_profiles/{user_id}` ([FastAPI-Tutorial](https://fastapi.tiangolo.com/tutorial/first-steps/)).
2. Response ist ein Pydantic-Modell: vorerst `user_id`, `signal_count`, `last_seen_at` (aggregiert aus `profile_signals`), `interests: []` leer.
3. Unbekannte `user_id` ⇒ `404` (nicht `200` mit leerem Profil — warum? Notiert eure Begründung).

**Fertig, wenn:** `uv run fastapi dev` läuft und ein pytest mit [`TestClient`](https://fastapi.tiangolo.com/tutorial/testing/) 200- und 404-Fall abdeckt. **Kein LLM-Call in diesem Pfad.**

## Etappe C — LLM-Verdichtung (~45 min)

1. Pydantic-Schema `ProfileSummary` (`interests: list[str]` max. 5, `persona_summary: str` max. 2 Sätze, `travel_style: Literal["budget","comfort","luxury","unknown"]`).
2. Funktion `condense_profile(user_id)`: liest alle Signale, baut einen Prompt ("Antworte NUR mit JSON nach diesem Schema …"), ruft Bedrock `converse` auf (Muster aus Übung 03, Modell-ID aus der Env) und validiert mit `model_validate_json`.
3. Ungültiges JSON ⇒ **ein** Retry mit Fehlerhinweis im Prompt, danach aufgeben und loggen.
4. Der Worker aus Etappe A stößt die Verdichtung an, sobald ein Nutzer ≥ 5 unverdichtete Signale hat; Ergebnis landet in `user_profiles(user_id, interests, persona_summary, travel_style, updated_at)`. Die API liefert es aus.

**Fertig, wenn:** `simulate_user.py` + Worker-Lauf ⇒ `GET /user_profiles/{id}` zeigt echte, vom LLM extrahierte Interessen.
**Recherche:** Wie erzwingt man knappe, deterministische Antworten? (`temperature`, `maxTokens` in [`inferenceConfig`](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-parameters.html))

## Etappe D — Embedding & Empfehlungen (~30 min)

1. Seed-Skript legt ~20 Reiseangebote in eurem Kapitel-05-Store an (`title` + Beschreibungstext, embedded).
2. Nach jeder Verdichtung: `interests` als Text embedden (Fake-Embedding aus Kapitel 05 — gleiche Funktion wie der Katalog!) und Top-3-Angebote per Cosine-Suche materialisieren (`profile_recommendations`).
3. API-Response um `recommendations` erweitern.

**Fertig, wenn:** Ein Nutzer, der nur nach Strand sucht, bekommt erkennbar Strand-Angebote — und die API bleibt unter den 50 ms, weil alles vorberechnet ist.

## Abschlussrunde (Plenum)

- Zeigt euer Profil-JSON. Welche Etappe hat am meisten Zeit gekostet — und war es die, die ihr erwartet hättet?
- Wo würde diese Komponente in eurer echten Systemlandschaft stehen, und wer wären ihre Konsumenten?
- Ausblick Tag 2: Der Chat-Assistent wird dieses Profil als **Kontext** nutzen — Personalisierung ohne zusätzliches Training.
