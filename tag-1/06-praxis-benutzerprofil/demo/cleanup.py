"""Tear down every AWS resource of the profile component (throwaway design).

Run: uv run python cleanup.py
"""

from config import dynamodb_client, events_client, settings, sqs_client
from infra import RULE_NAME


def main() -> None:
    events = events_client()
    sqs = sqs_client()
    dynamodb = dynamodb_client()

    try:
        target_ids = [
            target["Id"]
            for target in events.list_targets_by_rule(
                Rule=RULE_NAME, EventBusName=settings.bus_name
            ).get("Targets", [])
        ]
        if target_ids:
            events.remove_targets(Rule=RULE_NAME, EventBusName=settings.bus_name, Ids=target_ids)
        events.delete_rule(Name=RULE_NAME, EventBusName=settings.bus_name)
        events.delete_event_bus(Name=settings.bus_name)
        print(f"deleted rule + bus {settings.bus_name}")
    except events.exceptions.ResourceNotFoundException:
        pass

    for queue_name in (settings.queue_name, settings.dlq_name):
        try:
            queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
            sqs.delete_queue(QueueUrl=queue_url)
            print(f"deleted queue {queue_name}")
        except sqs.exceptions.QueueDoesNotExist:
            continue

    for table in (settings.signals_table, settings.profiles_table):
        try:
            dynamodb.delete_table(TableName=table)
            print(f"deleted table {table}")
        except dynamodb.exceptions.ResourceNotFoundException:
            continue


if __name__ == "__main__":
    main()
