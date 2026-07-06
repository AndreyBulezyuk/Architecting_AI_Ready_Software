"""Solution stack for exercise 03: bucket + SQS queue with DLQ + SSM parameter."""

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class ParticipantStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        bucket = s3.Bucket(
            self,
            "DataBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # a DLQ is itself a plain sqs.Queue; sqs.DeadLetterQueue is only the *struct*
        # that attaches it to the main queue (see aws_cdk.aws_sqs.DeadLetterQueue docs)
        dlq = sqs.Queue(self, "AiJobsDlq", queue_name="ai-jobs-dlq")

        queue = sqs.Queue(
            self,
            "AiJobsQueue",
            queue_name="ai-jobs",
            # after 3 failed receives a message moves to the DLQ
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=dlq),
        )

        ssm.StringParameter(
            self,
            "QueueUrlParam",
            parameter_name="/training/participant/queue-url",
            string_value=queue.queue_url,
        )

        cdk.CfnOutput(self, "BucketName", value=bucket.bucket_name)
        cdk.CfnOutput(self, "QueueUrl", value=queue.queue_url)
