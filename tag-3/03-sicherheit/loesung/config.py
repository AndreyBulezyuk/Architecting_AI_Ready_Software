"""Settings for the security demo — RAG plus a Bedrock guardrail."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock.client import BedrockClient
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class SecuritySettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_region: str = "eu-west-1"
    embedding_model_id: str = "cohere.embed-multilingual-v3"
    embedding_dimensions: int = 1024
    chat_model_id: str = "eu.amazon.nova-lite-v1:0"

    chunk_max_chars: int = 600
    chunk_overlap_chars: int = 100

    guardrail_name: str = "t303-ueb-guardrail"


settings = SecuritySettings()


def bedrock_runtime_client() -> "BedrockRuntimeClient":
    profile = os.environ.get("AWS_PROFILE", "default")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]


def bedrock_client() -> "BedrockClient":
    """Control-plane client: create/delete guardrails (not runtime inference)."""
    profile = os.environ.get("AWS_PROFILE", "default")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock")  # pyright: ignore[reportUnknownMemberType]
