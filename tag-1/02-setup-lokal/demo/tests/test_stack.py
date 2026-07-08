"""Smoke tests: one test per service of the local stack.

Run with the stack up (docker compose up -d):  uv run pytest -v
"""

# boto3.client()/neo4j driver expose partially-untyped members; results are annotated instead
# pyright: reportUnknownMemberType=false

import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, cast

import boto3
from neo4j import GraphDatabase

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.literals import BucketLocationConstraintType

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


def test_neo4j_is_reachable() -> None:
    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    ) as driver:
        driver.verify_connectivity()
        record = driver.execute_query("RETURN 1 AS ok").records[0]
        assert record["ok"] == 1


def test_neo4j_vector_index_available() -> None:
    # proves the native vector index works — from tag-2 on it carries all embeddings
    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    ) as driver:
        driver.execute_query(
            "CREATE VECTOR INDEX smoke_embedding IF NOT EXISTS "
            "FOR (s:SmokeDoc) ON (s.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: 3, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        driver.execute_query("MATCH (s:SmokeDoc) DETACH DELETE s")
        driver.execute_query("CREATE (:SmokeDoc {embedding: [1.0, 0.0, 0.0]})")
        driver.execute_query("CALL db.awaitIndexes(60)")
        records = driver.execute_query(
            "CALL db.index.vector.queryNodes('smoke_embedding', 1, $query) "
            "YIELD score RETURN score",
            query=[1.0, 0.0, 0.0],
        ).records
        assert records and records[0]["score"] > 0.99


def test_localstack_s3_roundtrip() -> None:
    s3: "S3Client" = boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    bucket = f"smoke-test-{uuid.uuid4()}"  # unique name keeps the test re-runnable
    region = cast("BucketLocationConstraintType", settings.aws_region)
    s3.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": region},
    )
    s3.put_object(Bucket=bucket, Key="hello.txt", Body=b"ai-ready")
    body = s3.get_object(Bucket=bucket, Key="hello.txt")["Body"].read()
    assert body == b"ai-ready"
