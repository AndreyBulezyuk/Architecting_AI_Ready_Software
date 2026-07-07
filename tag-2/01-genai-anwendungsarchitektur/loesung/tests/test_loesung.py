"""Live tests (Haiku/Sonnet, temperature 0) — skipped without AWS credentials."""

import botocore.exceptions
import pytest
from config import bedrock_client, settings
from router import run_task
from tickets import SupportTicket, extract_ticket


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def test_router_picks_cheap_tier_for_summaries() -> None:
    result = run_task("summarize", "Der Flug war pünktlich, das Hotel sauber, alles gut.")
    assert result.model_id == settings.cheap_model_id
    assert result.text.strip()
    assert result.cost_usd > 0
    assert result.latency_ms > 0


def test_router_picks_strong_tier_for_drafts() -> None:
    result = run_task("draft", "Kunde beschwert sich über verspäteten Transfer.")
    assert result.model_id == settings.strong_model_id
    assert result.text.strip()


def test_ticket_contract_is_always_valid() -> None:
    # correctness of the category is model judgement — the CONTRACT is what we assert
    for message in (
        "Ich möchte mich beschweren: das Zimmer war trotz Bestätigung nicht reserviert!",
        "Wie wird das Wetter morgen in Lissabon?",
    ):
        ticket = extract_ticket(message)
        assert isinstance(ticket, SupportTicket)
        assert len(ticket.summary) <= 200


def test_off_topic_message_lands_in_kein_anliegen() -> None:
    ticket = extract_ticket("Wie wird das Wetter morgen?")
    assert ticket.category == "kein_anliegen"
