"""Settings: local Neo4j + Bedrock + SQS/DynamoDB for the async job path."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_sqs.client import SQSClient


class ServiceSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_region: str = "eu-west-1"
    embedding_model_id: str = "cohere.embed-multilingual-v3"
    embedding_dimensions: int = 1024
    chat_model_id: str = "eu.amazon.nova-lite-v1:0"

    chunk_max_chars: int = 600
    chunk_overlap_chars: int = 100

    jobs_queue_name: str = "t204-ask-jobs"
    answers_table: str = "t204-answers"


settings = ServiceSettings()


def _session() -> boto3.Session:
    profile = os.environ.get("AWS_PROFILE", "default")
    return boto3.Session(profile_name=profile, region_name=settings.aws_region)


def bedrock_client() -> "BedrockRuntimeClient":
    return _session().client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]


def sqs_client() -> "SQSClient":
    return _session().client("sqs")  # pyright: ignore[reportUnknownMemberType]


def dynamodb_client() -> "DynamoDBClient":
    return _session().client("dynamodb")  # pyright: ignore[reportUnknownMemberType]
