"""Settings: raw text in S3 (real AWS), metadata + vectors in local Neo4j."""

import os
from functools import lru_cache
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class StoreSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_region: str = "eu-west-1"
    raw_bucket: str = ""  # empty -> auto: t05-demo-raw-<account_id> (bucket names are global)

    embedding_dimensions: int = 16
    embedding_model: str = "fake-hash-v1"  # switched to a Bedrock model id on day 2
    vector_index_name: str = "document_embeddings"


settings = StoreSettings()


def _session() -> boto3.Session:
    profile = os.environ.get("AWS_PROFILE", "default")
    return boto3.Session(profile_name=profile, region_name=settings.aws_region)


def s3_client() -> "S3Client":
    return _session().client("s3")  # pyright: ignore[reportUnknownMemberType]


@lru_cache
def bucket_name() -> str:
    if settings.raw_bucket:
        return settings.raw_bucket
    account_id: str = _session().client("sts").get_caller_identity()["Account"]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return f"t05-demo-raw-{account_id}"
