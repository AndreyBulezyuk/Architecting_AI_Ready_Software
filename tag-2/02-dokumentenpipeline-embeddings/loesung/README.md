# Lösung T2/02

```bash
uv sync
uv run pytest -v          # 4 Live-Tests (Embeddings + Haiku; < 1 Cent)
uv run python rag.py      # zitierte Antwort auf der Konsole
```

Stolpersteine aus der Übung:

- **Hit-Rate@k** ([evaluation.py](evaluation.py)) misst nur Retrieval — ob die *Antwort* stimmt, misst erst Ragas an Tag 3 (Abschlussfrage 1).
- **Winzige Chunks** (150/0): einzelne Sätze matchen zwar semantisch, tragen aber keinen Kontext — der Test zeigt, dass sie **nie besser** sind als die 600/100-Konfiguration; auf größeren Korpora fallen sie deutlich ab.
- **Ehrliches Scheitern** ([rag.py](rag.py)): Der exakte Marker `KEINE_ANTWORT_IM_KONTEXT` macht das **Refusal** (die bewusste "das beantworte ich nicht"-Antwort des Modells) testbar — ein frei formuliertes "weiß ich leider nicht" kann kein Test zuverlässig prüfen.
- Die Chunk-Referenzen (`doc_id`, `seq`) wandern mit in die Antwort — morgen (GraphRAG) und übermorgen (Evals) brauchen wir genau diese Nachvollziehbarkeit.
