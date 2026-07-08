"""Infra for the profile component: bus -> rule -> queue (+DLQ) + two DynamoDB tables.

Run: uv run python infra.py    (create-if-missing, AWS-correct — see chapter 04)
"""

import json
from typing import TYPE_CHECKING

from config import dynamodb_client, events_client, settings, sqs_client

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mypy_boto3_sqs.literals import QueueAttributeNameType

RULE_NAME = "travelmate-events-to-profile-ueb"


def queue_arn(queue_url: str) -> str:
    attrs = sqs_client().get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    return attrs["Attributes"]["QueueArn"]


def create_or_update_queue(
    name: str, attributes: "Mapping[QueueAttributeNameType, str] | None" = None
) -> str:
    sqs = sqs_client()
    try:
        return sqs.create_queue(QueueName=name, Attributes=attributes or {})["QueueUrl"]
    except sqs.exceptions.QueueNameExists:
        queue_url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
        if attributes:
            sqs.set_queue_attributes(QueueUrl=queue_url, Attributes=attributes)
        return queue_url


def create_queues() -> tuple[str, str]:
    dlq_url = create_or_update_queue(settings.dlq_name)
    redrive = {"deadLetterTargetArn": queue_arn(dlq_url),
               "maxReceiveCount": str(settings.max_receive_count)}
    main_url = create_or_update_queue(
        settings.queue_name,
        {
            "VisibilityTimeout": str(settings.visibility_timeout_seconds),
            "RedrivePolicy": json.dumps(redrive),
        },
    )
    return main_url, dlq_url


def create_bus_and_rule(main_queue_url: str) -> None:
    events = events_client()
    try:
        events.create_event_bus(Name=settings.bus_name)
    except events.exceptions.ResourceAlreadyExistsException:
        pass
    # ONE consumer for both signal types — the profile builds on searches AND bookings
    rule_arn = events.put_rule(
        Name=RULE_NAME,
        EventBusName=settings.bus_name,
        EventPattern=json.dumps(
            {"source": ["travelmate"], "detail-type": ["SearchSubmitted", "BookingCreated"]}
        ),
        State="ENABLED",
    )["RuleArn"]
    main_arn = queue_arn(main_queue_url)
    events.put_targets(
        Rule=RULE_NAME,
        EventBusName=settings.bus_name,
        Targets=[{"Id": "profile-queue", "Arn": main_arn}],
    )
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "events.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": main_arn,
            "Condition": {"ArnEquals": {"aws:SourceArn": rule_arn}},
        }],
    }
    sqs_client().set_queue_attributes(
        QueueUrl=main_queue_url, Attributes={"Policy": json.dumps(policy)}
    )


def create_tables() -> None:
    dynamodb = dynamodb_client()
    existing = dynamodb.list_tables()["TableNames"]
    if settings.signals_table not in existing:
        dynamodb.create_table(
            TableName=settings.signals_table,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "signal_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "signal_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    if settings.profiles_table not in existing:
        dynamodb.create_table(
            TableName=settings.profiles_table,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    for table in (settings.signals_table, settings.profiles_table):
        dynamodb.get_waiter("table_exists").wait(TableName=table)


def setup() -> tuple[str, str]:
    main_url, dlq_url = create_queues()
    create_bus_and_rule(main_url)
    create_tables()
    return main_url, dlq_url


if __name__ == "__main__":
    main, dlq = setup()
    print(f"queue: {main}\ndlq:   {dlq}\nbus:   {settings.bus_name}")
