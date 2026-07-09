"""Seeds the 5-document corpus (with LLM-extracted entities) into Neo4j.

Run once before evaluate.py / compare_eval.py / the tests:
    uv run python store_setup.py
"""

import kg
from sample_docs import SAMPLE_DOCS


def seed_corpus() -> None:
    kg.init_schema()
    for doc_id, text in SAMPLE_DOCS.items():
        chunks, entities = kg.ingest_document(doc_id, text)
        print(f"{doc_id}: {chunks} chunks, {entities} entities")


if __name__ == "__main__":
    seed_corpus()
