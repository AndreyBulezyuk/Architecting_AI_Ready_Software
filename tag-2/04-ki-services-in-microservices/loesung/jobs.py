"""Async job plumbing: queue + answers table + submit/get/complete operations."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from config import dynamodb_client, settings, sqs_client


def setup() -> str:
    """Queue + answers table, create-if-missing; returns the queue URL."""
    queue_url = sqs_client().create_queue(QueueName=settings.jobs_queue_name)["QueueUrl"]
    dynamodb = dynamodb_client()
    if settings.answers_table not in dynamodb.list_tables()["TableNames"]:
        dynamodb.create_table(
            TableName=settings.answers_table,
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    dynamodb.get_waiter("table_exists").wait(TableName=settings.answers_table)
    return queue_url


def submit(question: str) -> str:
    """Persist the job as pending FIRST, then enqueue — never the other way round."""
    job_id = str(uuid.uuid4())
    dynamodb_client().put_item(
        TableName=settings.answers_table,
        Item={
            "job_id": {"S": job_id},
            "status": {"S": "pending"},
            "question": {"S": question},
            "submitted_at": {"S": datetime.now(UTC).isoformat()},
        },
    )
    queue_url = sqs_client().get_queue_url(QueueName=settings.jobs_queue_name)["QueueUrl"]
    sqs_client().send_message(
        QueueUrl=queue_url, MessageBody=json.dumps({"job_id": job_id, "question": question})
    )
    return job_id


def get(job_id: str) -> dict[str, Any] | None:
    item = dynamodb_client().get_item(
        TableName=settings.answers_table, Key={"job_id": {"S": job_id}}
    ).get("Item")
    if item is None:
        return None
    return {
        "job_id": job_id,
        "status": item["status"].get("S", "pending"),
        "answer": item.get("answer", {}).get("S"),
    }


def complete(job_id: str, answer_text: str) -> None:
    dynamodb_client().update_item(
        TableName=settings.answers_table,
        Key={"job_id": {"S": job_id}},
        UpdateExpression="SET #s = :done, answer = :answer, completed_at = :now",
        ExpressionAttributeNames={"#s": "status"},  # status is a DynamoDB reserved word
        ExpressionAttributeValues={
            ":done": {"S": "done"},
            ":answer": {"S": answer_text},
            ":now": {"S": datetime.now(UTC).isoformat()},
        },
    )
