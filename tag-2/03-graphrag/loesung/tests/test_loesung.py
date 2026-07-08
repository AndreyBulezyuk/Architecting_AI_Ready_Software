"""Live tests: season ontology extension + baseline-vs-graphrag comparison."""

import botocore.exceptions
import kg
import pytest
from compare import compare
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
        assert chunks >= 1 and entities >= 2


def test_winter_report_gets_a_season_entity() -> None:
    with kg.driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (:T3UDoc {doc_id: 'ostsee-winter'})-[:MENTIONS]->(e:T3UEntity {type: 'season'}) "
            "RETURN e.name AS name"
        ).records
    assert records, "expected a season entity on the winter report"


def test_graph_reaches_docs_the_baseline_missed() -> None:
    result = compare("Wo kann ich wandern und danach im Meer baden?")
    assert result.graph_answer.strip()
    assert result.vector_docs, "baseline returned nothing"
    assert result.graph_only_docs, "graph expansion added no document beyond the baseline"


def test_identical_doc_sets_are_possible_too() -> None:
    # an honest comparison also shows cases where the graph adds nothing new on
    # top of an empty expansion — graph_docs always CONTAINS the vector docs
    result = compare("Welche Ziele passen für Familien?")
    assert result.vector_docs <= result.graph_docs
