"""Chunk store on the Neo4j vector index: ingest chunks + top-k semantic search."""

from dataclasses import dataclass
from typing import LiteralString, cast

from neo4j import Driver, GraphDatabase

from chunking import chunk_text
from config import settings
from embeddings import embed_documents, embed_query

LABEL = "T4UChunk"
INDEX = "t4u_chunk_embeddings"


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


def init_schema() -> None:
    with driver() as neo4j:
        ddl = (
            f"CREATE VECTOR INDEX {INDEX} IF NOT EXISTS "
            f"FOR (c:{LABEL}) ON (c.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("CALL db.awaitIndexes(60)")


def ingest_document(doc_id: str, text: str) -> int:
    """Chunk + embed (one batched call) + store; returns the number of chunks."""
    chunks = chunk_text(text, settings.chunk_max_chars, settings.chunk_overlap_chars)
    vectors = embed_documents(chunks)
    with driver() as neo4j:
        neo4j.execute_query(
            f"MATCH (c:{LABEL} {{doc_id: $doc_id}}) DETACH DELETE c",
            doc_id=doc_id,
        )
        neo4j.execute_query(
            "UNWIND $rows AS row "
            f"CREATE (:{LABEL} {{doc_id: row.doc_id, seq: row.seq, text: row.text, "
            "embedding: row.embedding, embedding_model: row.model})",
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


def search(query: str, k: int = 3) -> list[Hit]:
    query_vector = embed_query(query)
    with driver() as neo4j:
        records = neo4j.execute_query(
            f"CALL db.index.vector.queryNodes('{INDEX}', $k, $query) "
            "YIELD node, score "
            "RETURN node.doc_id AS doc_id, node.seq AS seq, node.text AS text, score "
            "ORDER BY score DESC",
            k=k,
            query=query_vector,
        ).records
    return [Hit(r["doc_id"], r["seq"], r["text"], float(r["score"])) for r in records]
