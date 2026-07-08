"""Mini document store: S3 holds the raw text, Neo4j the metadata + vector.

Lifecycle (theorie.md, slide 3):
  upsert  -> raw text to S3, node marked stale (embedding removed = out of the index)
  reembed -> embeds all stale nodes from their S3 source
  search  -> top-k via the vector index (stale nodes have no embedding -> not indexed)
"""

from typing import LiteralString, cast

from neo4j import Driver, GraphDatabase

from config import bucket_name, s3_client, settings
from embeddings import embed


def driver() -> Driver:
    return GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def init_schema() -> None:
    s3 = s3_client()
    try:
        s3.create_bucket(
            Bucket=bucket_name(),
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )
    except (s3.exceptions.BucketAlreadyOwnedByYou, s3.exceptions.BucketAlreadyExists):
        pass
    with driver() as neo4j:
        # DDL cannot take parameters — index name/dimensions come from trusted settings
        ddl = (
            f"CREATE VECTOR INDEX {settings.vector_index_name} IF NOT EXISTS "
            "FOR (d:Document) ON (d.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("CALL db.awaitIndexes(60)")


def upsert_document(doc_id: str, title: str, body: str) -> None:
    """Write path: raw text to S3, node becomes stale — embedding happens later.
    Removing the embedding property takes the node out of the vector index."""
    key = f"documents/{doc_id}.txt"
    s3_client().put_object(Bucket=bucket_name(), Key=key, Body=body.encode())
    with driver() as neo4j:
        neo4j.execute_query(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title, d.s3_key = $key, d.stale = true,
                d.updated_at = datetime(), d.embedding = null
            """,
            id=doc_id,
            title=title,
            key=key,
        )


def reembed_stale() -> int:
    """Batch step: embed every stale document from its S3 source; returns count."""
    s3 = s3_client()
    with driver() as neo4j:
        records = neo4j.execute_query(
            "MATCH (d:Document) WHERE d.stale RETURN d.id AS id, d.s3_key AS s3_key"
        ).records
        for record in records:
            body = s3.get_object(Bucket=bucket_name(), Key=record["s3_key"])["Body"].read()
            neo4j.execute_query(
                """
                MATCH (d:Document {id: $id})
                SET d.embedding = $embedding, d.embedding_model = $model, d.stale = false
                """,
                id=record["id"],
                embedding=embed(body.decode()),
                model=settings.embedding_model,
            )
        neo4j.execute_query("CALL db.awaitIndexes(60)")  # index updates are applied async
    return len(records)


def search(query: str, k: int = 3) -> list[tuple[str, str]]:
    """Top-k over embedded documents; returns (id, title) pairs, best first."""
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
