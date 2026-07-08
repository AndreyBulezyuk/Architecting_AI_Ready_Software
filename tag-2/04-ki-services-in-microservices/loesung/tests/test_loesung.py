"""Solution tests: the async job path end to end (plus the sync contract).

Cleanup afterwards: uv run python cleanup.py
"""

# TestClient/boto3 expose partially-untyped members; assertions pin the shapes instead
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import time
import uuid

import botocore.exceptions
import jobs
import pytest
import store
import worker
from config import bedrock_client
from fastapi.testclient import TestClient
from sample_docs import SAMPLE_DOCS

from service import app

client = TestClient(app)


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")

queue_url: str = ""


@pytest.fixture(scope="module", autouse=True)
def environment() -> None:
    global queue_url
    queue_url = jobs.setup()
    store.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        store.ingest_document(doc_id, text)


def test_sync_ask_still_works() -> None:
    response = client.post("/v1/ask", json={"question": "Wo kann man mit Kindern baden?"})
    assert response.status_code == 200
    assert response.json()["sources"]


def test_async_job_lifecycle() -> None:
    submitted = client.post("/v1/ask-jobs", json={"question": "Wohin für eine Hüttentour?"})
    assert submitted.status_code == 202
    job_id = submitted.json()["job_id"]

    # pending immediately after submit — the answer does not exist yet
    assert client.get(f"/v1/ask-jobs/{job_id}").json()["status"] == "pending"

    for _ in range(6):  # the worker turns pending into done
        if worker.poll_once(queue_url) or (
            client.get(f"/v1/ask-jobs/{job_id}").json()["status"] == "done"
        ):
            break
        time.sleep(1)
    final = client.get(f"/v1/ask-jobs/{job_id}").json()
    assert final["status"] == "done"
    assert final["answer"] and final["answer"].strip()


def test_unknown_job_id_is_404() -> None:
    assert client.get(f"/v1/ask-jobs/{uuid.uuid4()}").status_code == 404
