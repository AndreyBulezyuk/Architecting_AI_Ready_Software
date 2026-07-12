"""Turn a Bedrock `usage` block into a real USD cost — including cached tokens.

Prices and cache multipliers verified against AWS docs (July 2026). ALWAYS
re-check before a training; per-token prices change:
  https://aws.amazon.com/bedrock/pricing/
  https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html

Cache multipliers (5-minute TTL, the default):
  - cache WRITE  = 1.25x the normal input price
  - cache READ   = 0.10x the normal input price   (~90 % cheaper)
Breakeven: if fewer than ~30 % of requests hit the cache, the 1.25x writes cost
more than the reads save.
"""

from dataclasses import dataclass

# USD per 1000 tokens (input, output) — EXAMPLE values, verify before every training
PRICE_PER_1K: dict[str, tuple[float, float]] = {
    "eu.amazon.nova-lite-v1:0": (0.00006, 0.00024),
    "eu.amazon.nova-pro-v1:0": (0.00020, 0.00080),
}

CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


@dataclass
class TokenCounts:
    """The four token figures Bedrock reports; cache fields default to 0."""

    input_tokens: int
    output_tokens: int
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class CostBreakdown:
    input_cost: float
    output_cost: float
    cache_write_cost: float
    cache_read_cost: float

    @property
    def total(self) -> float:
        return self.input_cost + self.output_cost + self.cache_write_cost + self.cache_read_cost


def cost_of(model_id: str, tokens: TokenCounts) -> CostBreakdown:
    price_in, price_out = PRICE_PER_1K.get(model_id, (0.0, 0.0))
    # Bedrock reports cache tokens SEPARATELY from input_tokens — the plain
    # input_tokens field already excludes what was served from / written to cache
    return CostBreakdown(
        input_cost=tokens.input_tokens / 1000 * price_in,
        output_cost=tokens.output_tokens / 1000 * price_out,
        cache_write_cost=tokens.cache_write_tokens / 1000 * price_in * CACHE_WRITE_MULTIPLIER,
        cache_read_cost=tokens.cache_read_tokens / 1000 * price_in * CACHE_READ_MULTIPLIER,
    )
