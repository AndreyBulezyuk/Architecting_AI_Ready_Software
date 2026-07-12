"""Live tests: KG construction, graph expansion, groundedness, and Langfuse tracing.

Slow-ish (~60-90 s): 5 documents = 5 extraction calls + embeddings + answers.
"""

import re
import time
import uuid

import botocore.exceptions
import graphrag
import kg
import pytest
from config import bedrock_client
from sample_docs import SAMPLE_DOCS
from tracing import flush


def _aws_available() -> bool:
    try:
        bedrock_client()
        return True
    except botocore.exceptions.BotoCoreError:
        return False


pytestmark = pytest.mark.skipif(not _aws_available(), reason="AWS credentials required")


@pytest.fixture(scope="module", autouse=True)
def corpus() -> None:
    kg.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        chunks, entities = kg.ingest_document(doc_id, text)
        assert chunks >= 1
        assert entities >= 2, f"{doc_id}: expected at least 2 extracted entities"


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------


def test_entities_are_shared_across_documents() -> None:
    with kg.driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (a:T3Doc)-[:MENTIONS]->(e:T3Entity)<-[:MENTIONS]-(b:T3Doc) "
            "WHERE a.doc_id < b.doc_id "
            "RETURN e.name AS name, a.doc_id AS a, b.doc_id AS b LIMIT 5"
        ).records
    assert records, "no shared entities — the graph is disconnected"


def test_graph_expansion_reaches_docs_vector_search_missed() -> None:
    hits = graphrag.vector_hits("anstrengende Bergtour mit Hüttenübernachtung", k=2)
    hit_docs = {chunk.doc_id for chunk in hits}
    assert "alpen" in hit_docs

    expansion = graphrag.graph_expansion(hit_docs)
    assert expansion, "graph expansion returned nothing"
    assert all(chunk.doc_id not in hit_docs for chunk in expansion)
    assert all(chunk.via.startswith("graph:") for chunk in expansion)


def test_answer_combines_vector_and_graph_context() -> None:
    result = graphrag.answer("Wo kann ich wandern und danach im Meer baden?")
    assert result.text.strip()
    assert "KEINE_ANTWORT_IM_KONTEXT" not in result.text
    assert len(result.doc_ids) >= 2, "expected context from more than one document"
    assert any(chunk.via.startswith("graph:") for chunk in result.context)


# ---------------------------------------------------------------------------
# Groundedness: KB-specific answers, refusal for out-of-KB questions
# ---------------------------------------------------------------------------


def test_answer_cites_sources_with_bracket_numbers() -> None:
    """The model must reference context chunks as [n] — proof it's grounded."""
    result = graphrag.answer("Was wird über die Algarve berichtet?")
    assert result.text.strip()
    citations = re.findall(r"\[(\d+)\]", result.text)
    assert citations, f"no [n] citations found in answer: {result.text[:200]}"
    max_cite = max(int(c) for c in citations)
    assert max_cite <= len(result.context), (
        f"citation [{max_cite}] exceeds {len(result.context)} context chunks"
    )


def test_answer_contains_kb_specific_facts() -> None:
    """The answer must contain a fact from the KB, not generic LLM knowledge."""
    result = graphrag.answer("Welche Höhenmeter muss man bei der Hüttentour bewältigen?")
    assert "800" in result.text or "1200" in result.text, (
        f"expected specific numbers from the Alpen report (800/1200 Höhenmeter), "
        f"got: {result.text[:300]}"
    )
    assert any("alpen" in c.doc_id for c in result.context), "Alpen report should be in the context"


def test_out_of_kb_question_gets_refusal() -> None:
    """The model must refuse to answer questions outside the travel corpus."""
    result = graphrag.answer("Was ist die Hauptstadt von Australien?")
    assert "KEINE_ANTWORT_IM_KONTEXT" in result.text, (
        f"expected refusal for out-of-KB question, got: {result.text[:300]}"
    )


# ---------------------------------------------------------------------------
# Langfuse tracing: verify spans are exported
# ---------------------------------------------------------------------------


def test_graphrag_flow_appears_in_langfuse() -> None:
    """Run a full GraphRAG answer, flush, and verify the trace landed in Langfuse."""
    from langfuse_api import observations_for_trace, traces_by_tag

    tag = f"test-graphrag-{uuid.uuid4()}"
    result = graphrag.answer(
        "Wo kann ich wandern und danach im Meer baden?",
        tags=[tag, "tag-2/03-test"],
    )
    flush()

    trace = None
    for _ in range(10):
        traces = traces_by_tag(tag)
        if traces:
            trace = traces[0]
            break
        time.sleep(1)

    if trace is None:
        pytest.skip("Langfuse trace not yet visible — ingestion may be delayed")

    observations = observations_for_trace(str(trace["id"]))
    names = {obs["name"] for obs in observations}
    assert "graphrag.answer" in names, f"expected graphrag.answer span, got: {names}"
    assert "vector_search" in names or "graph_expansion" in names, (
        f"expected retrieval spans, got: {names}"
    )
