"""Settings: S3 raw text + SQS events (real AWS), metadata + vectors in local Neo4j."""

import os
from functools import lru_cache
from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_sqs.client import SQSClient


class StoreSettings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "trainingpass"

    aws_region: str = "eu-west-1"
    raw_bucket: str = ""  # empty -> auto: t05-ueb-raw-<account_id> (bucket names are global)
    update_queue_name: str = "t05-ueb-doc-updated"

    embedding_dimensions: int = 16
    embedding_model: str = "fake-hash-v1"
    vector_index_name: str = "document_embeddings_ueb"


settings = StoreSettings()


def _session() -> boto3.Session:
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    return boto3.Session(profile_name=profile, region_name=settings.aws_region)


def s3_client() -> "S3Client":
    return _session().client("s3")  # pyright: ignore[reportUnknownMemberType]


def sqs_client() -> "SQSClient":
    return _session().client("sqs")  # pyright: ignore[reportUnknownMemberType]


@lru_cache
def bucket_name() -> str:
    if settings.raw_bucket:
        return settings.raw_bucket
    account_id: str = _session().client("sts").get_caller_identity()["Account"]  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return f"t05-ueb-raw-{account_id}"
