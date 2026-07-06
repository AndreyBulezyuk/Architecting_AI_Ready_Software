"""Consume events from the queue: validate -> process -> delete (only on success).

Run: uv run python worker.py          # one polling round
Invalid messages are NOT deleted — after max_receive_count receives SQS moves
them to the DLQ (the retry behaviour from theorie.md, slide 4).
"""

import json

from pydantic import ValidationError

from config import settings, sqs_client
from models import SearchSubmitted


def handle_event(event: SearchSubmitted) -> None:
    # placeholder business logic; chapter 06 turns this into real profile updates
    print(f"profile update for {event.user_id}: searched {event.query!r}")


def poll_once(queue_url: str) -> tuple[int, int]:
    """One receive round; returns (processed, failed)."""
    sqs = sqs_client()
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2
    )
    processed = failed = 0
    for message in response.get("Messages", []):
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        if body is None or receipt_handle is None:  # optional in the API contract
            failed += 1
            continue
        try:
            # EventBridge envelope -> our payload lives in "detail"
            envelope = json.loads(body)
            event = SearchSubmitted.model_validate(envelope["detail"])
        except (ValidationError, KeyError, json.JSONDecodeError) as error:
            print(f"poison message, leaving for retry/DLQ: {error}")
            failed += 1
            continue  # no delete -> retry, then DLQ
        handle_event(event)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        processed += 1
    return processed, failed


if __name__ == "__main__":
    url = sqs_client().get_queue_url(QueueName=settings.queue_name)["QueueUrl"]
    ok, bad = poll_once(url)
    print(f"processed={ok} failed={bad}")
