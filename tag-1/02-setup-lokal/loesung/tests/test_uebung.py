"""Solution for exercise 02: one test per task (A: DynamoDB, B: pgvector, C: Neo4j)."""

# boto3.client()/neo4j driver expose partially-untyped members; results are annotated instead
# pyright: reportUnknownMemberType=false

import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import psycopg
from neo4j import GraphDatabase

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.client import DynamoDBClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


def test_a_dynamodb_user_profile_roundtrip() -> None:
    dynamodb: "DynamoDBClient" = boto3.client(
        "dynamodb",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    table = "user_profiles"
    existing = dynamodb.list_tables()["TableNames"]
    if table not in existing:
        dynamodb.create_table(
            TableName=table,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    # create_table is async — wait until the table is ACTIVE before writing
    dynamodb.get_waiter("table_exists").wait(TableName=table)

    user_id = f"user-{uuid.uuid4()}"
    dynamodb.put_item(
        TableName=table,
        Item={
            "user_id": {"S": user_id},
            "name": {"S": "Ada"},
            "interests": {"L": [{"S": "graphs"}, {"S": "events"}]},
        },
    )
    # response fields are optional in the API contract — access them defensively
    item = dynamodb.get_item(TableName=table, Key={"user_id": {"S": user_id}}).get("Item")
    assert item is not None
    assert item["name"].get("S") == "Ada"
    interests = item["interests"].get("L") or []
    assert [v.get("S") for v in interests] == ["graphs", "events"]


def test_b_pgvector_similarity_search() -> None:
    with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute("DROP TABLE IF EXISTS snippets")
        conn.execute("CREATE TABLE snippets (id serial PRIMARY KEY, text text, embedding vector(4))")
        conn.execute(
            "INSERT INTO snippets (text, embedding) VALUES "
            "('dog',    '[1, 0, 0, 0]'),"
            "('puppy',  '[0.9, 0.1, 0, 0]'),"
            "('car',    '[0, 0, 1, 0]'),"
            "('banana', '[0, 0, 0, 1]'),"
            "('wolf',   '[0.8, 0.2, 0, 0]')"
        )
        # <=> is cosine distance (lower = more similar); <-> would be L2 distance
        rows = conn.execute(
            "SELECT text FROM snippets ORDER BY embedding <=> '[1, 0.05, 0, 0]' LIMIT 2"
        ).fetchall()
        assert [r[0] for r in rows] == ["dog", "puppy"]


def test_c_neo4j_knows_relationship() -> None:
    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    ) as driver:
        driver.execute_query("MATCH (p:Person) DETACH DELETE p")
        driver.execute_query(
            "CREATE (:Person {name: 'Ada'})-[:KNOWS]->(:Person {name: 'Grace'})"
        )
        records = driver.execute_query(
            "MATCH (:Person {name: 'Ada'})-[:KNOWS]->(friend:Person) RETURN friend.name AS name"
        ).records
        assert [r["name"] for r in records] == ["Grace"]
