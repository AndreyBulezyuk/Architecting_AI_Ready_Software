"""Assertion tests: prove the synthesized template has the intended properties.

`cdk synth` only proves the code runs — these tests pin down WHAT it produces.
Run: uv run pytest -v
"""

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from participant_stack import ParticipantStack


def synth_template() -> Template:
    app = cdk.App()
    return Template.from_stack(ParticipantStack(app, "Participant"))


def test_queue_has_dlq_with_three_receives() -> None:
    template = synth_template()
    template.resource_count_is("AWS::SQS::Queue", 2)
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "QueueName": "ai-jobs",
            "RedrivePolicy": Match.object_like({"maxReceiveCount": 3}),
        },
    )


def test_bucket_is_private_encrypted_and_versioned() -> None:
    template = synth_template()
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "VersioningConfiguration": {"Status": "Enabled"},
            "PublicAccessBlockConfiguration": Match.object_like(
                {"BlockPublicAcls": True, "BlockPublicPolicy": True}
            ),
        },
    )


def test_queue_url_is_published_to_ssm() -> None:
    template = synth_template()
    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/training/participant/queue-url"},
    )
