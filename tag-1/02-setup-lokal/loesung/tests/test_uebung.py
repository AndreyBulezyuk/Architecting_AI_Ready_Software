"""Solution for exercise 02: A DynamoDB (LocalStack), B Neo4j vector index, C Neo4j graph."""

# boto3.client()/neo4j driver expose partially-untyped members; results are annotated instead
# pyright: reportUnknownMemberType=false

import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
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


def test_b_neo4j_vector_similarity_search() -> None:
    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    ) as driver:
        driver.execute_query(
            "CREATE VECTOR INDEX snippets_embedding IF NOT EXISTS "
            "FOR (s:Snippet) ON (s.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: 4, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        driver.execute_query("MATCH (s:Snippet) DETACH DELETE s")
        driver.execute_query(
            """
            UNWIND [
                {text: 'dog',    embedding: [1.0, 0.0, 0.0, 0.0]},
                {text: 'puppy',  embedding: [0.9, 0.1, 0.0, 0.0]},
                {text: 'car',    embedding: [0.0, 0.0, 1.0, 0.0]},
                {text: 'banana', embedding: [0.0, 0.0, 0.0, 1.0]},
                {text: 'wolf',   embedding: [0.8, 0.2, 0.0, 0.0]}
            ] AS row
            CREATE (:Snippet {text: row.text, embedding: row.embedding})
            """
        )
        # the vector index populates asynchronously — wait before the first query
        driver.execute_query("CALL db.awaitIndexes(60)")
        records = driver.execute_query(
            "CALL db.index.vector.queryNodes('snippets_embedding', 2, $query) "
            "YIELD node, score RETURN node.text AS text ORDER BY score DESC",
            query=[1.0, 0.05, 0.0, 0.0],
        ).records
        assert [record["text"] for record in records] == ["dog", "puppy"]


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
        assert [record["name"] for record in records] == ["Grace"]
