"""Assertions for the extended stack — each exercise addition gets its own proof."""

import aws_cdk as cdk
from aws_cdk import assertions
from stacks.neo4j_stack import Neo4jStack


def _template() -> assertions.Template:
    app = cdk.App()
    stack = Neo4jStack(app, "Neo4j", allowed_cidr="203.0.113.0/24")
    return assertions.Template.from_stack(stack)


def test_data_volume_is_encrypted() -> None:
    _template().has_resource_properties(
        "AWS::EC2::Instance",
        {"BlockDeviceMappings": assertions.Match.array_with([
            assertions.Match.object_like(
                {"Ebs": assertions.Match.object_like({"Encrypted": True})}
            )
        ])},
    )


def test_instance_has_ssm_session_manager_access() -> None:
    # the managed policy is attached to the instance role — SSM admin without SSH
    template = _template()
    roles = template.find_resources(
        "AWS::IAM::Role",
        {
            "Properties": {
                "ManagedPolicyArns": assertions.Match.array_with([
                    assertions.Match.object_like(
                        {"Fn::Join": assertions.Match.array_with([
                            assertions.Match.array_with(
                                [assertions.Match.string_like_regexp("AmazonSSMManagedInstanceCore")]
                            )
                        ])}
                    )
                ])
            }
        },
    )
    assert roles, "no role with the SSM Session Manager managed policy"


def test_no_ssh_port_is_open() -> None:
    # SSM Session Manager means port 22 should never be exposed
    open_ssh = _template().find_resources(
        "AWS::EC2::SecurityGroup",
        {
            "Properties": {
                "SecurityGroupIngress": assertions.Match.array_with(
                    [assertions.Match.object_like({"FromPort": 22})]
                )
            }
        },
    )
    assert open_ssh == {}, "port 22 is open — use SSM Session Manager instead"


def test_both_ssm_parameters_exist() -> None:
    template = _template()
    template.has_resource_properties(
        "AWS::SSM::Parameter", {"Name": "/training/neo4j/bolt-uri"}
    )
    template.has_resource_properties(
        "AWS::SSM::Parameter", {"Name": "/training/neo4j/browser-url"}
    )


def test_still_no_nat_gateway() -> None:
    # the cost guardrail must survive every extension
    _template().resource_count_is("AWS::EC2::NatGateway", 0)
