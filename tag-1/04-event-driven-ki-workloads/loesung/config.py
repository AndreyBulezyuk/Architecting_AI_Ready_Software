"""Environment-driven AWS connection settings (same pattern as the demo)."""

from typing import TYPE_CHECKING

import boto3
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_events.client import EventBridgeClient
    from mypy_boto3_sqs.client import SQSClient


class PipelineSettings(BaseSettings):
    aws_endpoint_url: str | None = None  # None -> real AWS
    aws_region: str = "eu-west-1"

    bus_name: str = "t04-demo-bus"  # reuse the demo bus
    booking_queue_name: str = "t04-ueb-booking-events"
    booking_dlq_name: str = "t04-ueb-booking-events-dlq"
    dedup_table_name: str = "t04-ueb-processed-events"
    max_receive_count: int = 2
    visibility_timeout_seconds: int = 5


settings = PipelineSettings()


def sqs_client() -> "SQSClient":
    return boto3.client(  # pyright: ignore[reportUnknownMemberType]
        "sqs", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )


def events_client() -> "EventBridgeClient":
    return boto3.client(  # pyright: ignore[reportUnknownMemberType]
        "events", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )


def dynamodb_client() -> "DynamoDBClient":
    return boto3.client(  # pyright: ignore[reportUnknownMemberType]
        "dynamodb", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )
