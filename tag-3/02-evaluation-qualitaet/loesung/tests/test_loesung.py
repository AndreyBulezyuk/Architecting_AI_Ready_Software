"""Live test: both arms produce valid, well-formed Ragas scores.

Deliberately does NOT assert "GraphRAG scores higher" — on this 5-document
corpus it measurably does not (see README). The test only checks the mechanics:
both pipelines run, scores are in [0, 1], and graph expansion actually adds
context on top of the vector hits it starts from.
"""

import botocore.exceptions
import graphrag
import pytest
from config import bedrock_client
from compare_eval import compare
from eval_dataset import EVAL_QUESTIONS
from store_setup import seed_corpus


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    seed_corpus()


def test_graph_expansion_adds_context_on_top_of_vector_hits() -> None:
    question, _ = EVAL_QUESTIONS[0]
    baseline = graphrag.baseline_answer(question)
    graph = graphrag.answer(question)
    assert len(graph.context) > len(baseline.context)
    assert all(chunk.via == "vector" for chunk in baseline.context)
    assert any(chunk.via.startswith("graph:") for chunk in graph.context)


def test_both_arms_produce_valid_scores() -> None:
    baseline, graph = compare()
    assert len(baseline) == len(graph) == len(EVAL_QUESTIONS)
    for results in (baseline, graph):
        for result in results:
            assert 0.0 <= result.faithfulness <= 1.0
            assert 0.0 <= result.context_precision <= 1.0
            assert 0.0 <= result.context_recall <= 1.0
