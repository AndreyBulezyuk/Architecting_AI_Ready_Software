"""CDK app for the training. Stacks are added chapter by chapter."""

import aws_cdk as cdk

from stacks.base_stack import BaseStack

app = cdk.App()

BaseStack(app, "TrainingBase")

cdk.Tags.of(app).add("project", "ai-ready-training")
cdk.Tags.of(app).add("owner", "participant")

app.synth()
