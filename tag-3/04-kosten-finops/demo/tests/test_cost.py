"""Cost math is tested offline (deterministic); caching + tiering run live."""

import botocore.exceptions
import pytest
from caching import compare_cache
from config import bedrock_client
from cost import CACHE_READ_MULTIPLIER, TokenCounts, cost_of
from tiering import compare_tiers


def test_cost_of_uses_separate_cache_rates() -> None:
    # a call that wrote and read cache tokens — each priced by its own multiplier
    tokens = TokenCounts(
        input_tokens=100, output_tokens=50, cache_write_tokens=1000, cache_read_tokens=2000
    )
    model = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    breakdown = cost_of(model, tokens)
    price_in, price_out = 0.001, 0.005
    assert breakdown.input_cost == pytest.approx(100 / 1000 * price_in)
    assert breakdown.output_cost == pytest.approx(50 / 1000 * price_out)
    assert breakdown.cache_write_cost == pytest.approx(1000 / 1000 * price_in * 1.25)
    assert breakdown.cache_read_cost == pytest.approx(2000 / 1000 * price_in * CACHE_READ_MULTIPLIER)


def test_unknown_model_costs_zero_not_crash() -> None:
    assert cost_of("some-future-model", TokenCounts(input_tokens=100, output_tokens=0)).total == 0.0


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


needs_aws = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@needs_aws
def test_cached_call_is_far_cheaper_than_uncached() -> None:
    uncached, cached = compare_cache()
    assert cached.cache_read > 0  # the second cached call genuinely read the cache
    assert cached.cost_usd < uncached.cost_usd * 0.5  # dramatically cheaper


@needs_aws
def test_cheap_tier_is_cheaper_than_strong_tier() -> None:
    task = "Antworte mit genau einem Wort: Hallo"
    cheap, strong = compare_tiers(task)
    assert cheap.cost_usd < strong.cost_usd
