"""Settings for the solution — separate table, plus a chat model for answers."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class RagSettings(BaseSettings):
    postgres_dsn: str = "postgresql://postgres:trainingpass@localhost:5432/aiready"
    table_name: str = "t202_ueb_chunks"

    aws_region: str = "eu-west-1"
    embedding_model_id: str = "cohere.embed-multilingual-v3"
    embedding_dimensions: int = 1024
    chat_model_id: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

    chunk_max_chars: int = 600
    chunk_overlap_chars: int = 100


settings = RagSettings()


def bedrock_client() -> "BedrockRuntimeClient":
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]
