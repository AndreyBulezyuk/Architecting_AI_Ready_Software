# Demo T3/04 — Was ein Token kostet

Ablauf (~15 min): AWS-Profil aktiv. (Neo4j wird hier nicht gebraucht — es geht nur um LLM-Kosten.)

```bash
cd tag-3/04-kosten-finops/demo
uv sync
uv run python caching.py    # Prompt Caching: gecachter Call kostet ~10 % des ungecachten
uv run python tiering.py    # Haiku vs. Sonnet: dieselbe Klassifikation, mehrfacher Preis
uv run pytest -v            # Kosten-Mathe offline + Caching/Tiering live
```

**Wichtige Punkte:**

- [cost.py](cost.py): rechnet aus dem `usage`-Block von `converse` echte USD-Kosten — **inklusive** der separat abgerechneten Cache-Tokens. Cache-Write kostet **1,25×**, Cache-Read **0,10×** des normalen Input-Preises (verifiziert gegen die AWS-Doku). Die Preise sind Beispielwerte mit Quellen-Kommentar — vor jeder Schulung gegen die [Pricing-Seite](https://aws.amazon.com/bedrock/pricing/) prüfen.
- [caching.py](caching.py): `cachePoint` markiert das Ende des wiederverwendbaren Prefix (die große Wissensbasis). Der erste Call schreibt den Cache, der zweite liest ihn — **live gemessen: ~10 % der Kosten**. Die Demo vergleicht bewusst *ohne Cache* gegen *mit Cache* (nicht zwei Cache-Calls), damit das Ergebnis unabhängig von einem bereits warmen Cache deterministisch ist.
- [tiering.py](tiering.py): dieselbe Support-Klassifikation auf Haiku und Sonnet. Die Botschaft ist **nicht** "Sonnet ist besser", sondern "wissen, was Qualität kostet" — für Klassifikation/Zusammenfassung ist der billige Tier meist gleichwertig und um ein Vielfaches günstiger (Model-Router aus T2/01!).
- **`inputTokens` schließt Cache-Tokens aus:** Bedrock zählt `cacheReadInputTokens`/`cacheWriteInputTokens` getrennt — wer nur `inputTokens` summiert, unterschätzt die Kosten. Deshalb rechnet `cost.py` alle vier Felder.
