"""Service contract tests: happy path (live), validation and throttling (offline)."""

# TestClient/boto3 expose partially-untyped members; assertions pin the shapes instead
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import botocore.exceptions
import pytest
import rag
import store
from botocore.exceptions import ClientError
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


needs_aws = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    if not _aws_available():
        return
    store.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        store.ingest_document(doc_id, text)


@needs_aws
def test_healthz_is_cheap_and_green() -> None:
    assert client.get("/healthz").status_code == 200


@needs_aws
def test_ask_returns_versioned_contract_with_sources() -> None:
    response = client.post("/v1/ask", json={"question": "Wo kann man mit Kindern baden?"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1"
    assert body["answer"].strip() and not body["refused"]
    assert body["sources"], "expected source references"
    assert body["input_tokens"] > 0 and body["latency_ms"] > 0


def test_too_short_question_is_rejected_by_the_contract() -> None:
    assert client.post("/v1/ask", json={"question": "hi"}).status_code == 422


def test_throttling_maps_to_503_with_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    def throttle(question: str, k: int = 3) -> rag.RagResult:
        raise ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse"
        )

    monkeypatch.setattr(rag, "answer", throttle)
    response = client.post("/v1/ask", json={"question": "Wo kann man baden?"})
    assert response.status_code == 503
    assert response.headers.get("Retry-After") == "2"
