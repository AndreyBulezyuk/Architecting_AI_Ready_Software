"""Live tests against Bedrock (cheap Haiku calls, temperature 0).

Requires AWS credentials (profile `ai-training` or AWS_PROFILE) — skipped otherwise.
"""

import botocore.exceptions
import pytest
from chat import ask
from config import bedrock_client
from structured import TravelerProfile, extract_profile


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def test_ask_returns_text_and_usage() -> None:
    result = ask("Antworte mit genau einem Wort: Hallo")
    assert result.text.strip()
    assert result.input_tokens > 0
    assert result.output_tokens > 0


def test_structured_extraction_matches_schema() -> None:
    profile = extract_profile(
        "Max, 34 Jahre alt, wohnt in Berlin und interessiert sich für Wandern und Tauchen."
    )
    assert isinstance(profile, TravelerProfile)
    assert "max" in profile.name.lower()
    assert profile.age == 34
    assert profile.home_city and "berlin" in profile.home_city.lower()
    assert profile.interests, "expected at least one interest"
