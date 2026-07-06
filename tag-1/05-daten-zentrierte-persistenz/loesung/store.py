"""Document store where every write publishes a DocumentUpdated event (part 2).

The re-embed guard: embedding_stale is only cleared if updated_at has not
changed since the event was processed — a late event never overwrites a
newer pending change.
"""

import psycopg
from psycopg import sql

from config import s3_client, settings, sqs_client
from embeddings import embed, to_pgvector
from models import DocumentUpdated

TABLE = sql.Identifier(settings.table_name)


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn, autocommit=True)


def init_schema() -> str:
    """Create bucket, queue, table and index; returns the queue url."""
    s3 = s3_client()
    existing = [bucket.get("Name") for bucket in s3.list_buckets().get("Buckets", [])]
    if settings.raw_bucket not in existing:
        s3.create_bucket(
            Bucket=settings.raw_bucket,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )
    queue_url = sqs_client().create_queue(QueueName=settings.update_queue_name)["QueueUrl"]
    with connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    id text PRIMARY KEY,
                    title text NOT NULL,
                    s3_key text NOT NULL,
                    embedding vector({dimensions}),
                    embedding_model text,
                    embedding_stale boolean NOT NULL DEFAULT true,
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """
            ).format(table=TABLE, dimensions=sql.Literal(settings.embedding_dimensions))
        )
        conn.execute(
            sql.SQL(
                "CREATE INDEX IF NOT EXISTS {index} ON {table} "
                "USING hnsw (embedding vector_cosine_ops)"
            ).format(index=sql.Identifier(f"{settings.table_name}_embedding_hnsw"), table=TABLE)
        )
    return queue_url


def upsert_document(doc_id: str, title: str, body: str) -> None:
    """Write path: S3 + stale row + DocumentUpdated event on the queue."""
    key = f"documents/{doc_id}.txt"
    s3_client().put_object(Bucket=settings.raw_bucket, Key=key, Body=body.encode())
    with connect() as conn:
        conn.execute(
            sql.SQL(
                """
                INSERT INTO {table} (id, title, s3_key, embedding_stale, updated_at)
                VALUES (%s, %s, %s, true, now())
                ON CONFLICT (id) DO UPDATE
                    SET title = EXCLUDED.title, s3_key = EXCLUDED.s3_key,
                        embedding_stale = true, updated_at = now()
                """
            ).format(table=TABLE),
            (doc_id, title, key),
        )
    queue_url = sqs_client().get_queue_url(QueueName=settings.update_queue_name)["QueueUrl"]
    sqs_client().send_message(
        QueueUrl=queue_url,
        MessageBody=DocumentUpdated(document_id=doc_id).model_dump_json(),
    )


def reembed_document(doc_id: str) -> bool:
    """Embed exactly one document; returns False if it vanished meanwhile."""
    with connect() as conn:
        row = conn.execute(
            sql.SQL("SELECT s3_key, updated_at FROM {table} WHERE id = %s").format(table=TABLE),
            (doc_id,),
        ).fetchone()
        if row is None:
            return False
        s3_key, seen_updated_at = row
        body = s3_client().get_object(Bucket=settings.raw_bucket, Key=s3_key)["Body"].read()
        # guard: only clear the flag if no newer write happened in between
        conn.execute(
            sql.SQL(
                """
                UPDATE {table}
                   SET embedding = %s, embedding_model = %s, embedding_stale = false
                 WHERE id = %s AND updated_at = %s
                """
            ).format(table=TABLE),
            (to_pgvector(embed(body.decode())), settings.embedding_model, doc_id,
             seen_updated_at),
        )
    return True


def search(query: str, k: int = 3) -> list[tuple[str, str]]:
    with connect() as conn:
        rows = conn.execute(
            sql.SQL(
                """
                SELECT id, title FROM {table}
                 WHERE NOT embedding_stale
                 ORDER BY embedding <=> %s::vector
                 LIMIT %s
                """
            ).format(table=TABLE),
            (to_pgvector(embed(query)), k),
        ).fetchall()
    return [(row[0], row[1]) for row in rows]
