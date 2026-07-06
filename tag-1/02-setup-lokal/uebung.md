# Übung 02 — Eigene Umgebung aufbauen und beweisen

**Ziel:** Jeder Teilnehmer hat den lokalen Stack laufen, versteht die uv-Arbeitsweise und kann Services programmatisch ansprechen.
**Zeit:** ~60 min einzeln. **Voraussetzung:** Docker Desktop, [uv installiert](https://docs.astral.sh/uv/getting-started/installation/), Repo geklont.

## Teil 1 — Nachziehen (≈15 min)

1. Stack starten: `docker compose up -d` im Repo-Root, warten bis `docker compose ps` überall `healthy` zeigt.
2. Demo-Tests bei euch ausführen: `cd tag-1/02-setup-lokal/demo && uv sync && uv run pytest -v` → 3× grün.
3. Neo4j Browser öffnen (<http://localhost:7474>, Login `neo4j`/`trainingpass`) und `RETURN "hallo" AS gruss` ausführen.

## Teil 2 — Eigenes Projekt (≈45 min)

Legt **neben** der Demo ein eigenes uv-Projekt an (`uv init mein-stack --bare` oder analog zur Demo) und implementiert als pytest-Tests:

### Aufgabe A — DynamoDB-Profiltabelle (LocalStack)

1. Erstellt per boto3 eine DynamoDB-Tabelle `user_profiles` (Partition Key `user_id`, On-Demand-Billing).
2. Schreibt ein Item mit `user_id`, `name` und einer Liste `interests`; lest es zurück und prüft die Felder.
3. **Achtung, Recherche nötig:** boto3 braucht gegen LocalStack einen `endpoint_url`-Parameter — und `create_table` ist asynchron: die Tabelle muss erst `ACTIVE` sein ([Waiter-Doku](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/waiter/TableExists.html)).

### Aufgabe B — Ähnlichkeitssuche mit pgvector

1. Erstellt eine Tabelle `snippets(id serial, text text, embedding vector(4))` — Extension nicht vergessen ([pgvector-README](https://github.com/pgvector/pgvector#getting-started)).
2. Fügt 4–5 Zeilen mit von Hand gewählten 4-dimensionalen "Embeddings" ein (z. B. `[1,0,0,0]` für "Hund", `[0.9,0.1,0,0]` für "Welpe" …).
3. Findet zu einem Query-Vektor die 2 ähnlichsten Zeilen. **Recherche:** Welcher Operator ist Cosine Distance, welcher L2? Sortiert die Treffer korrekt.

### Aufgabe C — Kanten in Neo4j

1. Legt per Python-Driver zwei `Person`-Knoten und eine `KNOWS`-Beziehung an ([Driver-Doku](https://neo4j.com/docs/python-manual/current/)).
2. Fragt per Cypher ab: "Wen kennt Person A?" und asserted das Ergebnis.
3. Schaut euch den Graphen im Neo4j Browser an (`MATCH (n) RETURN n`).

## Abschlussfragen (im Plenum)

- Was passiert mit euren DynamoDB-Tabellen nach `docker compose down`? Und mit den Neo4j-Daten? Warum ist das unterschiedlich? (Tipp: `volumes:` im Compose-File lesen.)
- Welche der drei Ablagen (KV, Vektor, Graph) würdet ihr für die TravelMate-Features aus Übung 01 jeweils einsetzen?

## Hinweise

- Alle Credentials/Endpoints wie in `demo/config.py` — kopiert euch die Settings-Klasse ruhig.
- Wer hängt: erst 5 min Doku-Links oben, dann Trainer fragen. Die Lösung in `loesung/` ist für **danach**.
