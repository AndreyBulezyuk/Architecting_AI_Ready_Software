"""Extended Neo4j stack (exercise solution): encrypted volume + SSM Session Manager
access (no SSH key) + a second SSM parameter for the browser URL.

Every addition over the demo is backed by an assertions test — infrastructure is
tested like application code.
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from constructs import Construct

NEO4J_BOLT_PORT = 7687
NEO4J_HTTP_PORT = 7474


class Neo4jStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, allowed_cidr: str) -> None:
        super().__init__(scope, construct_id)

        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=1,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                )
            ],
        )

        security_group = ec2.SecurityGroup(
            self, "Neo4jSg", vpc=vpc, description="Neo4j bolt + browser", allow_all_outbound=True
        )
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(allowed_cidr), ec2.Port.tcp(NEO4J_BOLT_PORT), "bolt"
        )
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(allowed_cidr), ec2.Port.tcp(NEO4J_HTTP_PORT), "browser"
        )

        # instance role with SSM Session Manager access — admin without an SSH key
        # (no port 22 open, no key pair to leak)
        # pyright can't see through jsii's decorator-based interface declaration:
        # ServicePrincipal/Role DO implement IPrincipal/IRole at runtime (synth passes)
        role = iam.Role(
            self,
            "Neo4jRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),  # pyright: ignore[reportArgumentType]
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ],
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "dnf install -y docker",
            "systemctl enable --now docker",
            "docker run -d --restart unless-stopped --name neo4j "
            f"-p {NEO4J_BOLT_PORT}:{NEO4J_BOLT_PORT} -p {NEO4J_HTTP_PORT}:{NEO4J_HTTP_PORT} "
            "-e NEO4J_AUTH=neo4j/trainingpass -v /data/neo4j:/data neo4j:5.26-community",
        )

        instance = ec2.Instance(
            self,
            "Neo4j",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.SMALL),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64
            ),
            security_group=security_group,
            role=role,  # pyright: ignore[reportArgumentType]  (jsii IRole, see above)
            user_data=user_data,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    # exercise addition: encryption at rest
                    volume=ec2.BlockDeviceVolume.ebs(
                        20, delete_on_termination=True, encrypted=True
                    ),
                )
            ],
        )

        ssm.StringParameter(
            self,
            "BoltUri",
            parameter_name="/training/neo4j/bolt-uri",
            string_value=f"bolt://{instance.instance_public_ip}:{NEO4J_BOLT_PORT}",
        )
        # exercise addition: a second parameter for the browser URL
        ssm.StringParameter(
            self,
            "BrowserUrl",
            parameter_name="/training/neo4j/browser-url",
            string_value=f"http://{instance.instance_public_ip}:{NEO4J_HTTP_PORT}",
        )

        cdk.CfnOutput(self, "Neo4jPublicIp", value=instance.instance_public_ip)
