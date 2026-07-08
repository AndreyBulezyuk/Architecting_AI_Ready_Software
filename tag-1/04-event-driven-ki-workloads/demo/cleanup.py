"""Tear down every resource this demo creates (throwaway design, slide 6).

Run: uv run python cleanup.py
Note: SQS blocks reusing a queue name for ~60 s after deletion.
"""

from config import events_client, settings, sqs_client


def main() -> None:
    events = events_client()
    sqs = sqs_client()

    for rule in events.list_rules(EventBusName=settings.bus_name).get("Rules", []):
        rule_name = rule.get("Name")
        assert rule_name is not None
        target_ids = [
            target["Id"]
            for target in events.list_targets_by_rule(
                Rule=rule_name, EventBusName=settings.bus_name
            ).get("Targets", [])
        ]
        if target_ids:
            events.remove_targets(Rule=rule_name, EventBusName=settings.bus_name, Ids=target_ids)
        events.delete_rule(Name=rule_name, EventBusName=settings.bus_name)
        print(f"deleted rule {rule_name}")
    events.delete_event_bus(Name=settings.bus_name)
    print(f"deleted bus {settings.bus_name}")

    for queue_name in (settings.queue_name, settings.dlq_name):
        try:
            queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
        except sqs.exceptions.QueueDoesNotExist:
            continue
        sqs.delete_queue(QueueUrl=queue_url)
        print(f"deleted queue {queue_name}")


if __name__ == "__main__":
    main()
