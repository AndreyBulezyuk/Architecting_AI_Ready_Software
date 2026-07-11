"""Settings: local Neo4j vector index, real Bedrock for embeddings."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class RagSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_region: str = "eu-west-1"
    # verified July 2026 — multilingual, batches of up to 96 texts, input_type support
    embedding_model_id: str = "cohere.embed-multilingual-v3"
    embedding_dimensions: int = 1024

    cheap_model_id: str = "eu.amazon.nova-lite-v1:0"
    strong_model_id: str = "eu.amazon.nova-lite-v1:0"
    chat_model_id: str = "eu.amazon.nova-lite-v1:0"

    chunk_max_chars: int = 600
    chunk_overlap_chars: int = 100


settings = RagSettings()


def bedrock_client() -> "BedrockRuntimeClient":
    profile = os.environ.get("AWS_PROFILE", "default")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]
