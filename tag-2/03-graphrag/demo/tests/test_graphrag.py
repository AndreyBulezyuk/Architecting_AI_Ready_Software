"""Live tests: KG construction (entities via forced tool call) + graph expansion.

Slow-ish (~60-90 s): 5 documents = 5 extraction calls + embeddings + 1 answer.
"""

import botocore.exceptions
import graphrag
import kg
import pytest
from config import bedrock_client
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
    kg.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        chunks, entities = kg.ingest_document(doc_id, text)
        assert chunks >= 1
        assert entities >= 2, f"{doc_id}: expected at least 2 extracted entities"


def test_entities_are_shared_across_documents() -> None:
    # the whole point of the graph: at least one entity connects two documents
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
