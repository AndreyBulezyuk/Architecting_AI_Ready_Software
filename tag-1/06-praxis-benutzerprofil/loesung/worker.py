"""Profile worker: SQS -> dedup signal write -> threshold -> LLM summarization ->
profile + vector recommendations. 5 events = ONE llm call, not five.

Run: uv run python worker.py
"""

import json
from datetime import UTC, datetime
from typing import Any

from catalog import recommend
from summarize import summarize_profile
from config import dynamodb_client, settings, sqs_client


def store_signal(user_id: str, signal_id: str, kind: str, payload: str) -> bool:
    """Idempotent write (chapter 04 pattern): False if the signal was seen before."""
    dynamodb = dynamodb_client()
    try:
        dynamodb.put_item(
            TableName=settings.signals_table,
            Item={
                "user_id": {"S": user_id},
                "signal_id": {"S": signal_id},
                "kind": {"S": kind},
                "payload": {"S": payload},
                "summarized": {"BOOL": False},
                "occurred_at": {"S": datetime.now(UTC).isoformat()},
            },
            ConditionExpression="attribute_not_exists(signal_id)",
        )
        return True
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return False


def fresh_signals(user_id: str) -> list[dict[str, Any]]:
    response = dynamodb_client().query(
        TableName=settings.signals_table,
        KeyConditionExpression="user_id = :u",
        FilterExpression="summarized = :f",
        ExpressionAttributeValues={":u": {"S": user_id}, ":f": {"BOOL": False}},
    )
    return list(response.get("Items", []))


def summarize_user(user_id: str) -> None:
    """Threshold reached: one LLM call over ALL fresh signals, then materialize."""
    signals = fresh_signals(user_id)
    lines = [f"{item['kind'].get('S')}: {item['payload'].get('S')}" for item in signals]
    summary = summarize_profile(lines)
    recommendations = recommend(summary.interests)

    dynamodb = dynamodb_client()
    dynamodb.put_item(
        TableName=settings.profiles_table,
        Item={
            "user_id": {"S": user_id},
            "interests": {"L": [{"S": interest} for interest in summary.interests]},
            "persona_summary": {"S": summary.persona_summary},
            "travel_style": {"S": summary.travel_style},
            "recommendations": {"L": [{"S": offer_id} for offer_id in recommendations]},
            "updated_at": {"S": datetime.now(UTC).isoformat()},
        },
    )
    for item in signals:  # mark as summarized so the next threshold starts fresh
        signal_id = item["signal_id"].get("S")
        assert signal_id is not None
        dynamodb.update_item(
            TableName=settings.signals_table,
            Key={"user_id": {"S": user_id}, "signal_id": {"S": signal_id}},
            UpdateExpression="SET summarized = :t",
            ExpressionAttributeValues={":t": {"BOOL": True}},
        )


def poll_once(queue_url: str) -> tuple[int, int]:
    """Returns (stored, duplicates); triggers summarization when the threshold is hit."""
    sqs = sqs_client()
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2)
    stored = duplicates = 0
    for message in response.get("Messages", []):
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        if body is None or receipt_handle is None:
            continue
        envelope = json.loads(body)  # EventBridge envelope around our event
        detail = envelope.get("detail", {})
        kind = envelope.get("detail-type", "unknown")
        user_id = detail.get("user_id")
        event_id = detail.get("event_id")
        if not user_id or not event_id:
            print(f"poison message, leaving for DLQ retry: {body[:120]}")
            continue
        payload = detail.get("query") or detail.get("destination") or ""
        if store_signal(user_id, event_id, kind, payload):
            stored += 1
        else:
            duplicates += 1
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        if len(fresh_signals(user_id)) >= settings.summarize_threshold:
            summarize_user(user_id)
            print(f"summarized profile for {user_id}")
    return stored, duplicates


if __name__ == "__main__":
    url = sqs_client().get_queue_url(QueueName=settings.queue_name)["QueueUrl"]
    total_stored = total_duplicates = 0
    for _ in range(5):
        stored, duplicates = poll_once(url)
        total_stored += stored
        total_duplicates += duplicates
    print(f"stored={total_stored} duplicates={total_duplicates}")
