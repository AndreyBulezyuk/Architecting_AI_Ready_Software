"""Solution tests along the exercise stages A -> B -> C/D.

Slow by design (~40-60 s): real EventBridge/SQS path + one Bedrock condensation.
Cleanup afterwards: uv run python cleanup.py
"""

# TestClient/boto3 expose partially-untyped members; assertions pin the shapes instead
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import time
import uuid

import botocore.exceptions
import infra
import pytest
import simulate_user
import worker
from catalog import seed_catalog
from config import dynamodb_client, settings, sqs_client
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def _aws_available() -> bool:
    try:
        sqs_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")

user_id = f"user-{uuid.uuid4()}"
main_url: str = ""


@pytest.fixture(scope="module", autouse=True)
def pipeline() -> None:
    """Etappe A setup + one full run: 6 events (1 duplicate) through the worker."""
    global main_url
    main_url, _ = infra.setup()
    assert seed_catalog() == 20

    assert simulate_user.simulate(user_id) == 6  # 5 unique + 1 duplicate

    stored = duplicates = 0
    for _ in range(12):
        new_stored, new_duplicates = worker.poll_once(main_url)
        stored += new_stored
        duplicates += new_duplicates
        if stored >= 5 and duplicates >= 1:
            break
        time.sleep(1)
    assert stored == 5, "expected exactly the 5 unique events to be stored"
    assert duplicates == 1, "the duplicate must be detected, not stored twice"


def test_a_dedup_leaves_exactly_five_signals() -> None:
    items = dynamodb_client().query(
        TableName=settings.signals_table,
        KeyConditionExpression="user_id = :u",
        ExpressionAttributeValues={":u": {"S": user_id}},
    ).get("Items", [])
    assert len(items) == 5


def test_b_unknown_user_is_404() -> None:
    assert client.get(f"/user_profiles/user-{uuid.uuid4()}").status_code == 404


def test_b_profile_aggregates_signals() -> None:
    response = client.get(f"/user_profiles/{user_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["signal_count"] == 5
    assert body["last_seen_at"]  # ISO timestamp of the newest signal


def test_cd_summarized_profile_with_recommendations() -> None:
    body = client.get(f"/user_profiles/{user_id}").json()
    assert 1 <= len(body["interests"]) <= 5
    assert body["travel_style"] in {"budget", "comfort", "luxury", "unknown"}
    assert len(body["recommendations"]) == settings.recommendation_count
    beach_offers = {"algarve-familie", "nordsee-watt", "kreta-resort",
                    "ligurien-kueste", "schwarzwald-familie", "garda-sport"}
    assert beach_offers & set(body["recommendations"]), body["recommendations"]
