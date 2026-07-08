"""End-to-end test of the reference component (AWS + Bedrock + local Neo4j).

Slow by design (~30-60 s): events flow through the real EventBridge/SQS path.
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
from config import sqs_client
from fastapi.testclient import TestClient

from api import app


def _aws_available() -> bool:
    try:
        sqs_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


def test_events_to_profile_to_api() -> None:
    main_url, _ = infra.setup()
    assert seed_catalog() == 20
    user_id = f"user-{uuid.uuid4()}"

    client = TestClient(app)
    assert client.get(f"/user_profiles/{user_id}").status_code == 404  # no profile yet

    assert simulate_user.simulate(user_id) == 6  # 5 unique + 1 duplicate

    stored = duplicates = 0
    for _ in range(12):
        new_stored, new_duplicates = worker.poll_once(main_url)
        stored += new_stored
        duplicates += new_duplicates
        if stored >= 5 and duplicates >= 1:
            break
        time.sleep(1)
    assert stored == 5
    assert duplicates == 1

    response = client.get(f"/user_profiles/{user_id}")
    assert response.status_code == 200
    profile = response.json()
    assert 1 <= len(profile["interests"]) <= 5
    assert profile["travel_style"] in {"budget", "comfort", "luxury", "unknown"}
    assert len(profile["recommendations"]) == 3
    # the simulated user only ever searched for beach+family — the vector
    # recommendations must reflect that (catalog ids are speaking names)
    beach_offers = {"algarve-familie", "nordsee-watt", "kreta-resort",
                    "ligurien-kueste", "schwarzwald-familie", "garda-sport"}
    assert beach_offers & set(profile["recommendations"]), profile["recommendations"]
