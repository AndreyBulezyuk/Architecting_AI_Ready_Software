"""Job worker: consumes ask-jobs, produces answers (the async half of the service).

Run: uv run python worker.py
"""

import json

import jobs
import rag
from config import settings, sqs_client


def poll_once(queue_url: str) -> int:
    sqs = sqs_client()
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=2)
    completed = 0
    for message in response.get("Messages", []):
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        if body is None or receipt_handle is None:
            continue
        payload = json.loads(body)
        result = rag.answer(payload["question"])
        jobs.complete(payload["job_id"], result.text)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        completed += 1
    return completed


if __name__ == "__main__":
    url = sqs_client().get_queue_url(QueueName=settings.jobs_queue_name)["QueueUrl"]
    print(f"completed {poll_once(url)} job(s)")
