"""Settings and clients for the exercise solution — own resource names (t06-ueb-…),
so demo and exercise never collide in AWS or in the shared local Neo4j."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_events.client import EventBridgeClient
    from mypy_boto3_sqs.client import SQSClient


class ProfileSettings(BaseSettings):
    aws_region: str = "eu-west-1"

    bus_name: str = "t06-ueb-bus"
    queue_name: str = "t06-ueb-profile-events"
    dlq_name: str = "t06-ueb-profile-events-dlq"
    signals_table: str = "t06-ueb-profile-signals"
    profiles_table: str = "t06-ueb-user-profiles"
    max_receive_count: int = 3
    visibility_timeout_seconds: int = 5

    # LLM summarization: cheap tier, id verified July 2026 (override via env)
    bedrock_model_id: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    summarize_threshold: int = 5

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"
    embedding_dimensions: int = 16
    offer_index_name: str = "ueb_offer_embeddings"  # one vector index per label+property
    recommendation_count: int = 3


settings = ProfileSettings()


def _session() -> boto3.Session:
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    return boto3.Session(profile_name=profile, region_name=settings.aws_region)


def sqs_client() -> "SQSClient":
    return _session().client("sqs")  # pyright: ignore[reportUnknownMemberType]


def events_client() -> "EventBridgeClient":
    return _session().client("events")  # pyright: ignore[reportUnknownMemberType]


def dynamodb_client() -> "DynamoDBClient":
    return _session().client("dynamodb")  # pyright: ignore[reportUnknownMemberType]


def bedrock_client() -> "BedrockRuntimeClient":
    return _session().client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]
