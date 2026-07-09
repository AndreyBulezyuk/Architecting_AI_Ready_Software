"""Prove the Neo4j stack via aws_cdk.assertions — synth alone is NOT proof.

These tests run fully offline (no AWS, no deploy): they synthesize the stack to a
CloudFormation template and assert the load-bearing properties. This is the
CLAUDE.md rule for CDK — the important properties get an assertions test.
"""

import aws_cdk as cdk
from aws_cdk import assertions
from stacks.neo4j_stack import Neo4jStack


def _template() -> assertions.Template:
    app = cdk.App()
    stack = Neo4jStack(app, "Neo4j", allowed_cidr="203.0.113.0/24")
    return assertions.Template.from_stack(stack)


def test_uses_the_cheap_arm_instance_type() -> None:
    _template().has_resource_properties(
        "AWS::EC2::Instance", {"InstanceType": "t4g.small"}
    )


def test_no_nat_gateway_is_created() -> None:
    # a NAT gateway would cost more than the instance itself — the cost trap
    _template().resource_count_is("AWS::EC2::NatGateway", 0)


def test_bolt_and_browser_are_restricted_to_the_allowed_cidr() -> None:
    # the ingress rules are inlined into the SecurityGroup (fixed-peer add_ingress_rule)
    self_cidr = assertions.Match.array_with([
        assertions.Match.object_like(
            {"CidrIp": "203.0.113.0/24", "FromPort": 7687, "ToPort": 7687}
        ),
        assertions.Match.object_like(
            {"CidrIp": "203.0.113.0/24", "FromPort": 7474, "ToPort": 7474}
        ),
    ])
    _template().has_resource_properties(
        "AWS::EC2::SecurityGroup", {"SecurityGroupIngress": self_cidr}
    )


def test_bolt_is_never_open_to_the_world() -> None:
    # explicit negative assertion: no inline ingress rule allows 0.0.0.0/0
    open_rules = _template().find_resources(
        "AWS::EC2::SecurityGroup",
        {
            "Properties": {
                "SecurityGroupIngress": assertions.Match.array_with(
                    [assertions.Match.object_like({"CidrIp": "0.0.0.0/0"})]
                )
            }
        },
    )
    assert open_rules == {}, "a security group rule exposes the database to the world"


def test_data_volume_is_disposable() -> None:
    _template().has_resource_properties(
        "AWS::EC2::Instance",
        {"BlockDeviceMappings": assertions.Match.array_with([
            assertions.Match.object_like(
                {"Ebs": assertions.Match.object_like({"DeleteOnTermination": True})}
            )
        ])},
    )


def test_publishes_the_bolt_uri_as_ssm_parameter() -> None:
    _template().has_resource_properties(
        "AWS::SSM::Parameter", {"Name": "/training/neo4j/bolt-uri"}
    )
