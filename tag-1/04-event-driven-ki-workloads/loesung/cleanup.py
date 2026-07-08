"""Tear down the solution's resources (booking rule, queues, dedup table).

The shared bus t04-demo-bus belongs to the demo — clean it via demo/cleanup.py.
Run: uv run python cleanup.py
"""

from config import dynamodb_client, events_client, settings, sqs_client
from infra import BOOKING_RULE


def main() -> None:
    events = events_client()
    sqs = sqs_client()
    dynamodb = dynamodb_client()

    try:
        target_ids = [
            target["Id"]
            for target in events.list_targets_by_rule(
                Rule=BOOKING_RULE, EventBusName=settings.bus_name
            ).get("Targets", [])
        ]
        if target_ids:
            events.remove_targets(Rule=BOOKING_RULE, EventBusName=settings.bus_name, Ids=target_ids)
        events.delete_rule(Name=BOOKING_RULE, EventBusName=settings.bus_name)
        print(f"deleted rule {BOOKING_RULE}")
    except events.exceptions.ResourceNotFoundException:
        pass

    for queue_name in (settings.booking_queue_name, settings.booking_dlq_name):
        try:
            queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
        except sqs.exceptions.QueueDoesNotExist:
            continue
        sqs.delete_queue(QueueUrl=queue_url)
        print(f"deleted queue {queue_name}")

    try:
        dynamodb.delete_table(TableName=settings.dedup_table_name)
        print(f"deleted table {settings.dedup_table_name}")
    except dynamodb.exceptions.ResourceNotFoundException:
        pass


if __name__ == "__main__":
    main()
