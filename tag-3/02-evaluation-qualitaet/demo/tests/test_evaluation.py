"""Live test: the baseline must score reasonably well on its own eval set —
if this ever drops sharply, something in retrieval or the prompt broke."""

import botocore.exceptions
import pytest
import store
from config import bedrock_client
from evaluate import evaluate_baseline
from sample_docs import SAMPLE_DOCS


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    store.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        store.ingest_document(doc_id, text)


def test_baseline_scores_well_on_its_own_questions() -> None:
    results = evaluate_baseline()
    assert len(results) == 3

    avg_faithfulness = sum(r.faithfulness for r in results) / len(results)
    avg_context_recall = sum(r.context_recall for r in results) / len(results)

    # a healthy baseline on its own well-matched questions should clear this —
    # a hard failure here means retrieval or the prompt regressed, not "bad luck"
    assert avg_faithfulness >= 0.7, f"faithfulness dropped to {avg_faithfulness:.2f}"
    assert avg_context_recall >= 0.7, f"context_recall dropped to {avg_context_recall:.2f}"
