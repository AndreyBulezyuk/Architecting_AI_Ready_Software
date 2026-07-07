"""Bedrock settings with a cheap and a strong tier (both verified July 2026)."""

import os
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class BedrockSettings(BaseSettings):
    aws_region: str = "eu-west-1"
    cheap_model_id: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    strong_model_id: str = "eu.anthropic.claude-sonnet-4-6"


# EXAMPLE prices in USD per 1M tokens (input, output) — check the pricing page
# before every training, prices change: https://aws.amazon.com/bedrock/pricing/
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "eu.anthropic.claude-haiku-4-5-20251001-v1:0": (1.0, 5.0),
    "eu.anthropic.claude-sonnet-4-6": (3.0, 15.0),
}

settings = BedrockSettings()


def bedrock_client() -> "BedrockRuntimeClient":
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    return session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]
