"""Neo4j-on-EC2 stack — the same container as the local docker-compose, in AWS.

Cost-conscious by design (see the Kosten-Radar in tag-1/03/trainer.md):
  - t4g.small (ARM, ~0.50 USD/day) — the ONLY hourly-priced resource we deploy
  - nat_gateways=0 + a PUBLIC subnet — a NAT Gateway would cost more than the instance
  - RemovalPolicy.DESTROY on the data volume — nothing survives `cdk destroy`

⚠️  This stack costs money per hour while running. Deploy only during the training
day and run `cdk destroy` at the end. This chapter PROVES the stack via assertions
(cdk synth + Template.from_stack) — it does NOT deploy it.
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ssm as ssm
from constructs import Construct

NEO4J_BOLT_PORT = 7687
NEO4J_HTTP_PORT = 7474


class Neo4jStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, allowed_cidr: str) -> None:
        super().__init__(scope, construct_id)

        # nat_gateways=0: the instance sits in a public subnet and gets a public IP;
        # a NAT gateway (default 1) would silently add ~1 USD/day — the classic trap
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
        # only the training participants' CIDR — never 0.0.0.0/0 for a database
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(allowed_cidr), ec2.Port.tcp(NEO4J_BOLT_PORT), "bolt"
        )
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(allowed_cidr), ec2.Port.tcp(NEO4J_HTTP_PORT), "browser"
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "dnf install -y docker",
            "systemctl enable --now docker",
            # the SAME image as the local docker-compose — local/cloud parity
            "docker run -d --restart unless-stopped --name neo4j "
            f"-p {NEO4J_BOLT_PORT}:{NEO4J_BOLT_PORT} -p {NEO4J_HTTP_PORT}:{NEO4J_HTTP_PORT} "
            "-e NEO4J_AUTH=neo4j/trainingpass -v /data/neo4j:/data neo4j:5.26-community",
        )

        instance = ec2.Instance(
            self,
            "Neo4j",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T4G, ec2.InstanceSize.SMALL
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64
            ),
            security_group=security_group,
            user_data=user_data,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        20, delete_on_termination=True  # nothing survives destroy
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

        cdk.CfnOutput(self, "Neo4jPublicIp", value=instance.instance_public_ip)
