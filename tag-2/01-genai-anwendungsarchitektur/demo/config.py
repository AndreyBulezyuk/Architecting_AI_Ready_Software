"""Bedrock connection settings.

Model ids are config, never code (tag-1/03). The defaults are inference profiles
verified in the training account (July 2026) — always re-check with:
    aws bedrock list-inference-profiles --region eu-west-1 \
        --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `eu.anthropic.claude`)].inferenceProfileId'
"""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class BedrockSettings(BaseSettings):
    aws_region: str = "eu-west-1"
    # cheap+fast tier for extraction/classification (override via env BEDROCK_MODEL_ID)
    bedrock_model_id: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"


settings = BedrockSettings()


def bedrock_client() -> "BedrockRuntimeClient":
    # profile binding as in tag-1/03: the `aws login` provider needs botocore[crt]
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]
