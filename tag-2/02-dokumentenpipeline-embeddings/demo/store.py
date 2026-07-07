"""Chunk store on pgvector: ingest chunks + top-k semantic search."""

from dataclasses import dataclass

import psycopg
from psycopg import sql

from chunking import chunk_text
from config import settings
from embeddings import embed_documents, embed_query, to_pgvector

TABLE = sql.Identifier(settings.table_name)


@dataclass
class Hit:
    doc_id: str
    seq: int
    text: str
    distance: float


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn, autocommit=True)


def init_schema() -> None:
    with connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    doc_id text NOT NULL,
                    seq int NOT NULL,
                    text text NOT NULL,
                    embedding vector({dimensions}) NOT NULL,
                    embedding_model text NOT NULL,
                    PRIMARY KEY (doc_id, seq)
                )
                """
            ).format(table=TABLE, dimensions=sql.Literal(settings.embedding_dimensions))
        )
        conn.execute(
            sql.SQL(
                "CREATE INDEX IF NOT EXISTS {index} ON {table} "
                "USING hnsw (embedding vector_cosine_ops)"
            ).format(index=sql.Identifier(f"{settings.table_name}_hnsw"), table=TABLE)
        )


def ingest_document(doc_id: str, text: str) -> int:
    """Chunk + embed (one batched call) + store; returns the number of chunks."""
    chunks = chunk_text(text, settings.chunk_max_chars, settings.chunk_overlap_chars)
    vectors = embed_documents(chunks)
    with connect() as conn:
        conn.execute(sql.SQL("DELETE FROM {table} WHERE doc_id = %s").format(table=TABLE), (doc_id,))
        for seq, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            conn.execute(
                sql.SQL(
                    "INSERT INTO {table} (doc_id, seq, text, embedding, embedding_model) "
                    "VALUES (%s, %s, %s, %s, %s)"
                ).format(table=TABLE),
                (doc_id, seq, chunk, to_pgvector(vector), settings.embedding_model_id),
            )
    return len(chunks)


def search(query: str, k: int = 3) -> list[Hit]:
    query_vector = to_pgvector(embed_query(query))
    with connect() as conn:
        rows = conn.execute(
            sql.SQL(
                """
                SELECT doc_id, seq, text, embedding <=> %s::vector AS distance
                  FROM {table}
                 ORDER BY distance
                 LIMIT %s
                """
            ).format(table=TABLE),
            (query_vector, k),
        ).fetchall()
    return [Hit(row[0], row[1], row[2], float(row[3])) for row in rows]
