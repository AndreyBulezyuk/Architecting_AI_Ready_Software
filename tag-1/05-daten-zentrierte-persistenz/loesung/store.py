"""Document store with event-driven re-embedding (exercise parts 2+3).

Differences to the demo: upsert publishes a DocumentUpdated event to SQS, and
re-embedding targets exactly one document instead of scanning all stale nodes.
"""

from typing import LiteralString, cast

from neo4j import Driver, GraphDatabase

from config import bucket_name, s3_client, settings, sqs_client
from embeddings import embed
from models import DocumentUpdated


def driver() -> Driver:
    return GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def init_schema() -> str:
    """Bucket + vector index + update queue; returns the queue URL."""
    s3 = s3_client()
    try:
        s3.create_bucket(
            Bucket=bucket_name(),
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )
    except (s3.exceptions.BucketAlreadyOwnedByYou, s3.exceptions.BucketAlreadyExists):
        pass
    with driver() as neo4j:
        ddl = (
            f"CREATE VECTOR INDEX {settings.vector_index_name} IF NOT EXISTS "
            "FOR (d:UebDocument) ON (d.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("CALL db.awaitIndexes(60)")
    return sqs_client().create_queue(QueueName=settings.update_queue_name)["QueueUrl"]


def upsert_document(doc_id: str, title: str, body: str) -> None:
    """Write path: S3 + stale node + DocumentUpdated event (no direct re-embed!)."""
    key = f"documents/{doc_id}.txt"
    s3_client().put_object(Bucket=bucket_name(), Key=key, Body=body.encode())
    with driver() as neo4j:
        neo4j.execute_query(
            """
            MERGE (d:UebDocument {id: $id})
            SET d.title = $title, d.s3_key = $key, d.stale = true,
                d.updated_at = datetime(), d.embedding = null
            """,
            id=doc_id,
            title=title,
            key=key,
        )
    sqs = sqs_client()
    queue_url = sqs.get_queue_url(QueueName=settings.update_queue_name)["QueueUrl"]
    sqs.send_message(QueueUrl=queue_url, MessageBody=DocumentUpdated(document_id=doc_id).model_dump_json())


def reembed_document(doc_id: str) -> bool:
    """Embed exactly one document from its S3 source; False if it vanished."""
    with driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (d:UebDocument {id: $id}) RETURN d.s3_key AS s3_key", id=doc_id
        ).records
        if not records:
            return False
        body = s3_client().get_object(Bucket=bucket_name(), Key=records[0]["s3_key"])["Body"].read()
        neo4j.execute_query(
            """
            MATCH (d:UebDocument {id: $id})
            SET d.embedding = $embedding, d.embedding_model = $model, d.stale = false
            """,
            id=doc_id,
            embedding=embed(body.decode()),
            model=settings.embedding_model,
        )
        neo4j.execute_query("CALL db.awaitIndexes(60)")  # index updates are applied async
    return True


def search(query: str, k: int = 3) -> list[tuple[str, str]]:
    with driver() as neo4j:
        records = neo4j.execute_query(
            "CALL db.index.vector.queryNodes($index, $k, $query) "
            "YIELD node, score "
            "RETURN node.id AS id, node.title AS title ORDER BY score DESC",
            index=settings.vector_index_name,
            k=k,
            query=embed(query),
        ).records
    return [(record["id"], record["title"]) for record in records]
