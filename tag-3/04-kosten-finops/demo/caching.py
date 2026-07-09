"""Prompt caching in action: a large, reused system prompt gets cached, and the
second call reads it back at 0.1x instead of reprocessing it.

`cachePoint` marks where the reusable prefix ends. Bedrock caches everything up to
that point; the next call within the TTL reads it instead of paying full input price.

Run: uv run python caching.py
"""

from dataclasses import dataclass

from config import bedrock_client, settings
from cost import TokenCounts, cost_of

# a big, stable "knowledge base" prefix — the kind of context you send on every
# request and would rather not pay for every single time
KNOWLEDGE_BASE = "Reisebericht-Wissensbasis von TravelMate.\n" + (
    "Die Algarve bietet flache, geschützte Buchten bei Lagos, ideal für Familien "
    "mit Kindern; außerhalb der Ferien kostet ein Apartment die Hälfte. " * 120
)


@dataclass
class CallStats:
    fresh_input: int
    cache_write: int
    cache_read: int
    cost_usd: float


def _ask(question: str, *, use_cache: bool) -> CallStats:
    system: list[dict[str, object]] = [{"text": KNOWLEDGE_BASE}]
    if use_cache:
        system.append({"cachePoint": {"type": "default"}})
    response = bedrock_client().converse(
        modelId=settings.chat_model_id,
        system=system,  # pyright: ignore[reportArgumentType]  (SystemContentBlock union)
        messages=[{"role": "user", "content": [{"text": question}]}],
        inferenceConfig={"maxTokens": 30, "temperature": 0},
    )
    usage = response["usage"]
    tokens = TokenCounts(
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        cache_write_tokens=usage.get("cacheWriteInputTokens", 0),
        cache_read_tokens=usage.get("cacheReadInputTokens", 0),
    )
    return CallStats(
        fresh_input=tokens.input_tokens,
        cache_write=tokens.cache_write_tokens,
        cache_read=tokens.cache_read_tokens,
        cost_usd=cost_of(settings.chat_model_id, tokens).total,
    )


def compare_cache(
    question: str = "Fasse die Wissensbasis in einem Satz zusammen.",
) -> tuple[CallStats, CallStats]:
    """Uncached baseline vs. a cached call — deterministic regardless of a warm cache.

    Two cached calls in a row would depend on whether the cache is already warm
    from an earlier run; comparing NO-cache against WITH-cache always shows the win.
    """
    uncached = _ask(question, use_cache=False)
    _ask(question, use_cache=True)  # prime the cache
    cached = _ask(question, use_cache=True)  # now a guaranteed read
    return uncached, cached


if __name__ == "__main__":
    uncached, cached = compare_cache()
    print(f"Ohne Cache: fresh={uncached.fresh_input} read={uncached.cache_read}  "
          f"${uncached.cost_usd:.6f}")
    print(f"Mit Cache:  fresh={cached.fresh_input} read={cached.cache_read}  "
          f"${cached.cost_usd:.6f}")
    if uncached.cost_usd:
        print(f"\nDer Cache-Read kostet {cached.cost_usd / uncached.cost_usd * 100:.0f} % "
              "des ungecachten Calls")
