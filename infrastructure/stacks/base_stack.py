"""Base stack deployed in tag-1/03: proves the CDK toolchain end-to-end."""

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class BaseStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # bucket = s3.Bucket(
        #     self,
        #     "DataBucket",
        #     block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        #     encryption=s3.BucketEncryption.S3_MANAGED,
        #     versioned=True,
        #     # training account: everything must be disposable without leftovers
        #     removal_policy=cdk.RemovalPolicy.DESTROY,
        #     auto_delete_objects=True,
        # )


        # ssm.StringParameter(
        #     self,
        #     "DataBucketNameParam",
        #     parameter_name="/training/base/data-bucket-name",
        #     string_value=bucket.bucket_name,
        # )

        # cdk.CfnOutput(self, "DataBucketName", value=bucket.bucket_name)
