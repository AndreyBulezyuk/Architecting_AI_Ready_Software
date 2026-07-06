"""Idempotent pipeline setup: bus -> rule -> queue (+ DLQ with redrive policy).

Run: uv run python infra.py
Everything is create-if-missing, so it is safe to run repeatedly (LocalStack loses
state on restart; in AWS this would normally live in CDK — done in the exercise).
"""

import json

from config import events_client, settings, sqs_client


def queue_arn(queue_url: str) -> str:
    attrs = sqs_client().get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    return attrs["Attributes"]["QueueArn"]


def create_queues() -> tuple[str, str]:
    """Create DLQ + main queue with redrive policy; returns (main_url, dlq_url)."""
    sqs = sqs_client()
    dlq_url = sqs.create_queue(QueueName=settings.dlq_name)["QueueUrl"]
    redrive = {"deadLetterTargetArn": queue_arn(dlq_url),
               "maxReceiveCount": str(settings.max_receive_count)}
    main_url = sqs.create_queue(
        QueueName=settings.queue_name,
        Attributes={
            "VisibilityTimeout": str(settings.visibility_timeout_seconds),
            "RedrivePolicy": json.dumps(redrive),
        },
    )["QueueUrl"]
    return main_url, dlq_url


def create_bus_and_rule(main_queue_url: str) -> None:
    """Bus + rule (source/detail-type filter) + queue target + queue policy."""
    events = events_client()
    try:
        events.create_event_bus(Name=settings.bus_name)
    except events.exceptions.ResourceAlreadyExistsException:
        pass  # create-if-missing: put_rule/put_targets below are naturally idempotent
    rule_arn = events.put_rule(
        Name="search-submitted-to-profile",
        EventBusName=settings.bus_name,
        EventPattern=json.dumps(
            {"source": ["travelmate"], "detail-type": ["SearchSubmitted"]}
        ),
        State="ENABLED",
    )["RuleArn"]

    main_arn = queue_arn(main_queue_url)
    events.put_targets(
        Rule="search-submitted-to-profile",
        EventBusName=settings.bus_name,
        Targets=[{"Id": "profile-queue", "Arn": main_arn}],
    )

    # real AWS enforces this policy (EventBridge must be allowed to send) —
    # LocalStack does not, which is exactly the local-vs-cloud gap from the slides
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


def setup() -> tuple[str, str]:
    main_url, dlq_url = create_queues()
    create_bus_and_rule(main_url)
    return main_url, dlq_url


if __name__ == "__main__":
    main, dlq = setup()
    print(f"queue: {main}\ndlq:   {dlq}\nbus:   {settings.bus_name}")
