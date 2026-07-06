"""Consume DocumentUpdated events and re-embed exactly the touched document."""

from pydantic import ValidationError

from config import settings, sqs_client
from models import DocumentUpdated
from store import reembed_document


def poll_once(queue_url: str) -> int:
    sqs = sqs_client()
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2)
    processed = 0
    for message in response.get("Messages", []):
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        if body is None or receipt_handle is None:
            continue
        try:
            event = DocumentUpdated.model_validate_json(body)
        except ValidationError as error:
            print(f"poison message, leaving for retry: {error}")
            continue
        reembed_document(event.document_id)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        processed += 1
    return processed


if __name__ == "__main__":
    url = sqs_client().get_queue_url(QueueName=settings.update_queue_name)["QueueUrl"]
    print(f"re-embedded {poll_once(url)} document(s)")
