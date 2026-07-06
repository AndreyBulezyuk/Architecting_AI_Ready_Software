"""Exercise infra: booking queue + own rule on the demo bus + dedup table.

Run: uv run python infra.py
"""

import json

from config import dynamodb_client, events_client, settings, sqs_client

BOOKING_RULE = "booking-created-to-booking-queue"


def queue_arn(queue_url: str) -> str:
    attrs = sqs_client().get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    return attrs["Attributes"]["QueueArn"]


def create_queues() -> tuple[str, str]:
    sqs = sqs_client()
    dlq_url = sqs.create_queue(QueueName=settings.booking_dlq_name)["QueueUrl"]
    redrive = {"deadLetterTargetArn": queue_arn(dlq_url),
               "maxReceiveCount": str(settings.max_receive_count)}
    main_url = sqs.create_queue(
        QueueName=settings.booking_queue_name,
        Attributes={
            "VisibilityTimeout": str(settings.visibility_timeout_seconds),
            "RedrivePolicy": json.dumps(redrive),
        },
    )["QueueUrl"]
    return main_url, dlq_url


def create_rule(booking_queue_url: str) -> None:
    events = events_client()
    try:
        events.create_event_bus(Name=settings.bus_name)
    except events.exceptions.ResourceAlreadyExistsException:
        pass

    # the pattern filters on detail-type: ONLY BookingCreated takes this route
    rule_arn = events.put_rule(
        Name=BOOKING_RULE,
        EventBusName=settings.bus_name,
        EventPattern=json.dumps(
            {"source": ["travelmate"], "detail-type": ["BookingCreated"]}
        ),
        State="ENABLED",
    )["RuleArn"]

    booking_arn = queue_arn(booking_queue_url)
    events.put_targets(
        Rule=BOOKING_RULE,
        EventBusName=settings.bus_name,
        Targets=[{"Id": "booking-queue", "Arn": booking_arn}],
    )
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "events.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": booking_arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": rule_arn}},
        }],
    }
    sqs_client().set_queue_attributes(
        QueueUrl=booking_queue_url, Attributes={"Policy": json.dumps(policy)}
    )


def create_dedup_table() -> None:
    dynamodb = dynamodb_client()
    if settings.dedup_table_name not in dynamodb.list_tables()["TableNames"]:
        dynamodb.create_table(
            TableName=settings.dedup_table_name,
            KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    dynamodb.get_waiter("table_exists").wait(TableName=settings.dedup_table_name)


def setup() -> tuple[str, str]:
    main_url, dlq_url = create_queues()
    create_rule(main_url)
    create_dedup_table()
    return main_url, dlq_url


if __name__ == "__main__":
    main, dlq = setup()
    print(f"booking queue: {main}\ndlq:           {dlq}\ndedup table:   {settings.dedup_table_name}")
