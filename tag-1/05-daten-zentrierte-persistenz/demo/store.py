"""Mini document store: S3 holds the raw text, Postgres the metadata + vector.

Lifecycle (theorie.md, slide 3):
  upsert  -> raw text to S3, row marked embedding_stale
  reembed -> embeds all stale rows in one batch
  search  -> top-k over non-stale rows only
"""

import psycopg
from psycopg import sql

from config import s3_client, settings
from embeddings import embed, to_pgvector


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn, autocommit=True)


def init_schema() -> None:
    s3 = s3_client()
    if settings.aws_endpoint_url:  # LocalStack accepts the location constraint too
        existing = [b.get("Name") for b in s3.list_buckets().get("Buckets", [])]
        if settings.raw_bucket not in existing:
            s3.create_bucket(
                Bucket=settings.raw_bucket,
                CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
            )
    with connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id text PRIMARY KEY,
                    title text NOT NULL,
                    s3_key text NOT NULL,
                    embedding vector({dimensions}),
                    embedding_model text,
                    embedding_stale boolean NOT NULL DEFAULT true,
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """
            ).format(dimensions=sql.Literal(settings.embedding_dimensions))
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS documents_embedding_hnsw "
            "ON documents USING hnsw (embedding vector_cosine_ops)"
        )


def upsert_document(doc_id: str, title: str, body: str) -> None:
    """Write path: raw text to S3, row becomes stale — embedding happens later."""
    key = f"documents/{doc_id}.txt"
    s3_client().put_object(Bucket=settings.raw_bucket, Key=key, Body=body.encode())
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, title, s3_key, embedding_stale, updated_at)
            VALUES (%s, %s, %s, true, now())
            ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title, s3_key = EXCLUDED.s3_key,
                    embedding_stale = true, updated_at = now()
            """,
            (doc_id, title, key),
        )


def reembed_stale() -> int:
    """Batch step: embed every stale document from its S3 source; returns count."""
    s3 = s3_client()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, s3_key FROM documents WHERE embedding_stale"
        ).fetchall()
        for doc_id, s3_key in rows:
            body = s3.get_object(Bucket=settings.raw_bucket, Key=s3_key)["Body"].read()
            conn.execute(
                """
                UPDATE documents
                   SET embedding = %s, embedding_model = %s, embedding_stale = false
                 WHERE id = %s
                """,
                (to_pgvector(embed(body.decode())), settings.embedding_model, doc_id),
            )
    return len(rows)


def search(query: str, k: int = 3) -> list[tuple[str, str]]:
    """Top-k over non-stale documents; returns (id, title) pairs, best first."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title FROM documents
             WHERE NOT embedding_stale
             ORDER BY embedding <=> %s::vector
             LIMIT %s
            """,
            (to_pgvector(embed(query)), k),
        ).fetchall()
    return [(row[0], row[1]) for row in rows]
