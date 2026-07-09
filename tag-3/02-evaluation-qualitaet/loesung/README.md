# Lösung T3/02

```bash
uv sync
uv run pytest -v              # ~2 min live: seedet den Korpus, beide Pipelines, 6 Bewertungen
uv run python compare_eval.py # dieselbe Auswertung lesbar auf der Konsole
```

## Das Ergebnis — und warum es zählt

Auf unserem **5-Dokumente-Korpus** mit `k=3`:

| Metrik | Baseline (Vector-RAG) | GraphRAG |
|---|---|---|
| Faithfulness | **0.88** | 0.82 |
| Context Precision | 1.00 | 1.00 |
| Context Recall | 1.00 | 1.00 |

**GraphRAG gewinnt hier nicht — reproduzierbar, nicht nur ein schlechter Lauf** (zweimal identisch gemessen). Der Grund ist mechanisch nachvollziehbar: Bei nur 5 Dokumenten holt `k=3` bereits **60 % des gesamten Korpus** — die Graph-Expansion fügt nur noch ein viertes Dokument hinzu, das nicht immer zur Frage passt und dadurch die Faithfulness leicht verwässert (mehr Kontext = mehr Gelegenheit für eine Aussage, die nicht direkt belegt ist).

**Das ist die eigentliche Lektion des Kapitels:** GraphRAGs Stärke ist Multi-Hop-Retrieval über einen Korpus, in dem Vector-Suche allein die relevanten Dokumente **nicht** findet. Bei einem kleinen Korpus mit großzügigem `k` ist dafür kein Raum — die Kosten aus T2/03 (LLM-Call pro Dokument beim Ingest) zahlen sich hier nicht aus. Ob sich GraphRAG lohnt, ist eine **empirische Frage pro Korpus und Fragentyp**, keine, die sich pauschal mit "Graph ist mächtiger" beantworten lässt.

## Woher kommen die Zahlen — Stolpersteine

- [ragas_bedrock.py](ragas_bedrock.py) (aus der Demo übernommen): Ragas' `InstructorLLM` muss **async** sein (`instructor.from_bedrock(..., async_client=True)`), sonst bricht jeder `.score()`-Aufruf mit `Cannot use agenerate() with a synchronous client`. Und `top_p` muss nach dem Bauen aus `model_args` gelöscht werden — Bedrocks Claude-Modelle lehnen `temperature` **und** `top_p` gleichzeitig ab, Ragas' Default schickt aber beide.
- [graphrag.py](graphrag.py): `baseline_answer()` ist **T2/03s** `vector_hits()` ohne `graph_expansion()` — dieselbe Retrieval-Funktion wie im Demo-GraphRAG, nur ein Schritt weniger. So bleibt der Vergleich fair: identisches Embedding-Modell, identischer Chat-Prompt, identisches `k`.
- [compare_eval.py](compare_eval.py): Beide Arme laufen durch **dieselben** Ragas-Metrik-Instanzen (ein `Faithfulness`, ein `ContextPrecision`, ein `ContextRecall`) — sonst wäre ein Unterschied im Ergebnis nicht dem RAG-Ansatz, sondern zwei verschiedenen Judge-Konfigurationen zuzuschreiben.
- **Eigene Neo4j-Labels** (`EvalDoc`/`EvalChunk`/`EvalEntity`, Index `eval_chunk_embeddings`): T2/03 hat in derselben lokalen Neo4j bereits `T3Doc`/`T3Chunk`/`T3Entity` belegt — eigene Labels verhindern Kollisionen.
