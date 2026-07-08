"""Chunk store on the Neo4j vector index — label and chunk parameters are injectable
so the chunking experiment (part 2) can ingest the same corpus twice.

One vector index per label+property: each experiment configuration gets its own label
(and thus its own index), e.g. UebChunk vs UebChunkTiny.
"""

from dataclasses import dataclass
from typing import LiteralString, cast

from neo4j import Driver, GraphDatabase

from chunking import chunk_text
from config import settings
from embeddings import embed_documents, embed_query

DEFAULT_LABEL = "UebChunk"


@dataclass
class Hit:
    doc_id: str
    seq: int
    text: str
    score: float  # similarity: higher = closer


def driver() -> Driver:
    return GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def _index_name(label: str) -> str:
    return f"{label.lower()}_embeddings"


def init_schema(label: str = DEFAULT_LABEL) -> None:
    with driver() as neo4j:
        ddl = (
            f"CREATE VECTOR INDEX {_index_name(label)} IF NOT EXISTS "
            f"FOR (c:{label}) ON (c.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("CALL db.awaitIndexes(60)")


def ingest_document(
    doc_id: str,
    text: str,
    *,
    label: str = DEFAULT_LABEL,
    max_chars: int | None = None,
    overlap_chars: int | None = None,
) -> int:
    chunks = chunk_text(
        text,
        max_chars if max_chars is not None else settings.chunk_max_chars,
        overlap_chars if overlap_chars is not None else settings.chunk_overlap_chars,
    )
    vectors = embed_documents(chunks)
    with driver() as neo4j:
        neo4j.execute_query(
            cast(LiteralString, f"MATCH (c:{label} {{doc_id: $doc_id}}) DETACH DELETE c"),
            doc_id=doc_id,
        )
        neo4j.execute_query(
            cast(
                LiteralString,
                "UNWIND $rows AS row "
                f"CREATE (:{label} {{doc_id: row.doc_id, seq: row.seq, text: row.text, "
                "embedding: row.embedding, embedding_model: row.model})",
            ),
            rows=[
                {
                    "doc_id": doc_id,
                    "seq": seq,
                    "text": chunk,
                    "embedding": vector,
                    "model": settings.embedding_model_id,
                }
                for seq, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ],
        )
        neo4j.execute_query("CALL db.awaitIndexes(60)")
    return len(chunks)


def search(query: str, k: int = 3, *, label: str = DEFAULT_LABEL) -> list[Hit]:
    query_vector = embed_query(query)
    with driver() as neo4j:
        records = neo4j.execute_query(
            cast(
                LiteralString,
                f"CALL db.index.vector.queryNodes('{_index_name(label)}', $k, $query) "
                "YIELD node, score "
                "RETURN node.doc_id AS doc_id, node.seq AS seq, node.text AS text, score "
                "ORDER BY score DESC",
            ),
            k=k,
            query=query_vector,
        ).records
    return [Hit(r["doc_id"], r["seq"], r["text"], float(r["score"])) for r in records]
