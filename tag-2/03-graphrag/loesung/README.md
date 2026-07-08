# Lösung T2/03

```bash
uv sync
uv run pytest -v            # Ingest (6 Docs mit season-Typ) + Vergleich
uv run python compare.py    # Baseline vs. GraphRAG auf der Konsole
```

Stolpersteine aus der Übung:

- **Drei Stellen für `season`** (Teil 2): Pydantic-`Literal` und Prompt — der Graph-Code bleibt unverändert, weil `type` nur ein Property ist. Genau dafür haben wir die Ontologie als Daten modelliert, nicht als Labels.
- **`season` verbindet (noch) nichts:** Nur der Ostsee-Bericht nennt eine Jahreszeit — eine Ontologie-Erweiterung nützt erst, wenn die **Daten sie abdecken**. Das ist die eigentliche Lektion aus Teil 2.3.
- **Re-Ingest & geteilte Entities** (Recherchefrage): Die `MENTIONS`-Kanten des Dokuments verschwinden mit `DETACH DELETE` des Doc-Knotens; die Entity-Knoten bleiben stehen, weil andere Dokumente sie referenzieren können — eine geteilte Entität "gehört" niemandem. Verwaiste Entities räumt man separat auf (`WHERE NOT (e)<-[:MENTIONS]-()`).
- **Vergleich** ([compare.py](compare.py)): `graph_docs` enthält die Vektor-Treffer immer (Expansion fügt nur hinzu) — der interessante Wert ist `graph_only_docs`. Die notierten Fragen + erwartete Antworten sind euer Ragas-Datensatz für Tag 3.
