"""End-to-end pipeline tests against LocalStack (docker compose up -d).

pytest forces the LocalStack endpoint itself — the production path stays untouched.
"""

# ruff: noqa: E402  (env vars must be set before the config module is imported)

import json
import os
import time
import uuid

os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ["VISIBILITY_TIMEOUT_SECONDS"] = "1"  # fast retries for the DLQ test

import infra
import producer
import worker
from config import sqs_client
from models import SearchSubmitted


def drain(queue_url: str) -> None:
    sqs = sqs_client()
    while messages := sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get(
        "Messages"
    ):
        for message in messages:
            receipt_handle = message.get("ReceiptHandle")
            assert receipt_handle is not None
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


def test_event_flows_from_bus_to_worker() -> None:
    main_url, dlq_url = infra.setup()
    drain(main_url)
    drain(dlq_url)

    query = f"hotel {uuid.uuid4()}"
    producer.publish(SearchSubmitted(user_id="user-1", query=query))

    processed = 0
    for _ in range(10):
        ok, _ = worker.poll_once(main_url)
        processed += ok
        if processed:
            break
    assert processed == 1


def test_poison_message_ends_up_in_dlq() -> None:
    main_url, dlq_url = infra.setup()
    drain(main_url)
    drain(dlq_url)

    sqs = sqs_client()
    sqs.send_message(QueueUrl=main_url, MessageBody=json.dumps({"detail": {"broken": True}}))

    # receive without deleting until SQS moves the message to the DLQ
    for _ in range(6):
        worker.poll_once(main_url)
        time.sleep(1.2)  # let the visibility timeout expire
        dlq_messages = sqs.receive_message(QueueUrl=dlq_url, MaxNumberOfMessages=1).get(
            "Messages", []
        )
        if dlq_messages:
            body = json.loads(dlq_messages[0].get("Body", "{}"))
            assert body["detail"] == {"broken": True}
            return
    raise AssertionError("poison message never reached the DLQ")
