"""Connection settings — defaults match the root docker-compose.yml."""

from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class StoreSettings(BaseSettings):
    postgres_dsn: str = "postgresql://postgres:trainingpass@localhost:5432/aiready"

    aws_endpoint_url: str | None = "http://localhost:4566"  # None -> real AWS/S3
    aws_region: str = "eu-west-1"
    raw_bucket: str = "t05-demo-raw-documents"

    embedding_dimensions: int = 16
    embedding_model: str = "fake-hash-v1"  # switched to a Bedrock model id on day 2


settings = StoreSettings()


def s3_client() -> "S3Client":
    if settings.aws_endpoint_url:  # LocalStack: fixed dummy credentials, no profile lookup
        return boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "s3",
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
    return boto3.client("s3", region_name=settings.aws_region)  # pyright: ignore[reportUnknownMemberType]
