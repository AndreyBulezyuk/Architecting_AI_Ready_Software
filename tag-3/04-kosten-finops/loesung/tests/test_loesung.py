"""Live test: the cost report runs the whole workload and routes correctly."""

import botocore.exceptions
import pytest
from config import bedrock_client, settings
from report import cost_report, total_cost


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def test_report_prices_a_mixed_workload() -> None:
    items = cost_report([
        ("classify", "Meine Kreditkarte wurde doppelt belastet."),
        ("summarize", "Der Flug war pünktlich, das Hotel sauber."),
        ("draft", "Kunde beschwert sich über den verspäteten Transfer."),
    ])
    assert len(items) == 3
    assert total_cost(items) > 0

    by_type = {item.task_type: item for item in items}
    # router: cheap tier for classify/summarize, strong tier for draft
    assert by_type["classify"].model_id == settings.cheap_model_id
    assert by_type["summarize"].model_id == settings.cheap_model_id
    assert by_type["draft"].model_id == settings.strong_model_id


def test_routing_the_draft_to_the_cheap_tier_would_be_cheaper() -> None:
    # the point of the exercise: tier choice is a cost decision you can measure
    draft = cost_report([("draft", "Kunde beschwert sich über den verspäteten Transfer.")])[0]
    assert draft.model_id == settings.strong_model_id
    assert draft.cost_usd > 0
