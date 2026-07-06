"""Idempotent worker: conditional put on the dedup table guards each event.

Duplicates are logged and DELETED from the queue (answer to closing question 1:
a duplicate is not an error — sending it to the DLQ would just create noise).
"""

import json

from pydantic import ValidationError

from config import dynamodb_client, settings, sqs_client
from models import BookingCreated


def claim_event(event: BookingCreated) -> bool:
    """True if we are the first to process this event_id (conditional put wins)."""
    dynamodb = dynamodb_client()
    try:
        dynamodb.put_item(
            TableName=settings.dedup_table_name,
            Item={"event_id": {"S": str(event.event_id)}},
            ConditionExpression="attribute_not_exists(event_id)",
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return False
    return True


def handle_event(event: BookingCreated) -> None:
    print(f"booking for {event.user_id}: {event.destination} ({event.price_eur} EUR)")


def poll_once(queue_url: str) -> tuple[int, int, int]:
    """One receive round; returns (processed, duplicates, failed)."""
    sqs = sqs_client()
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2
    )
    processed = duplicates = failed = 0
    for message in response.get("Messages", []):
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        if body is None or receipt_handle is None:
            failed += 1
            continue
        try:
            envelope = json.loads(body)
            event = BookingCreated.model_validate(envelope["detail"])
        except (ValidationError, KeyError, json.JSONDecodeError) as error:
            print(f"poison message, leaving for retry/DLQ: {error}")
            failed += 1
            continue

        if claim_event(event):
            handle_event(event)
            processed += 1
        else:
            print(f"duplicate {event.event_id}, skipping")
            duplicates += 1
        # in both cases the message leaves the queue — the work is accounted for
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    return processed, duplicates, failed


if __name__ == "__main__":
    url = sqs_client().get_queue_url(QueueName=settings.booking_queue_name)["QueueUrl"]
    ok, dup, bad = poll_once(url)
    print(f"processed={ok} duplicates={dup} failed={bad}")
