"""Solution tests against the participant's AWS account: routing filter + idempotency.

Resources stay after the run — remove them with:  uv run python cleanup.py
"""

# ruff: noqa: E402  (env vars must be set before the config module is imported)

import os
import uuid

os.environ.setdefault("AWS_PROFILE", "ai-training")
os.environ["VISIBILITY_TIMEOUT_SECONDS"] = "1"

import infra
import producer
import worker
from config import events_client, settings, sqs_client
from models import BookingCreated


def drain(queue_url: str) -> None:
    sqs = sqs_client()
    while messages := sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get(
        "Messages"
    ):
        for message in messages:
            receipt_handle = message.get("ReceiptHandle")
            assert receipt_handle is not None
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


def poll_totals(queue_url: str, rounds: int = 8) -> tuple[int, int]:
    processed = duplicates = 0
    for _ in range(rounds):
        ok, dup, _ = worker.poll_once(queue_url)
        processed += ok
        duplicates += dup
        if processed + duplicates >= 2:
            break
    return processed, duplicates


def test_duplicate_event_is_processed_exactly_once() -> None:
    main_url, dlq_url = infra.setup()
    drain(main_url)
    drain(dlq_url)

    event = BookingCreated(user_id="user-1", destination=f"trip-{uuid.uuid4()}", price_eur=100.0)
    producer.publish(event)
    producer.publish(event)  # duplicate on purpose

    processed, duplicates = poll_totals(main_url)
    assert processed == 1
    assert duplicates == 1


def test_search_events_do_not_reach_booking_queue() -> None:
    main_url, _ = infra.setup()
    drain(main_url)

    # a SearchSubmitted-shaped event must NOT match the BookingCreated rule
    events_client().put_events(
        Entries=[{
            "EventBusName": settings.bus_name,
            "Source": "travelmate",
            "DetailType": "SearchSubmitted",
            "Detail": '{"user_id": "user-1", "query": "hotel"}',
        }]
    )
    response = sqs_client().receive_message(
        QueueUrl=main_url, MaxNumberOfMessages=10, WaitTimeSeconds=3
    )
    assert response.get("Messages", []) == []
