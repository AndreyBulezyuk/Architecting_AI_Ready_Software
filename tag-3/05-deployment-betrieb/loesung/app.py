"""CDK app for the Neo4j-on-EC2 deployment (tag-3/05).

  npx cdk synth              # offline: Python -> CloudFormation
  npx cdk deploy Neo4j       # ⚠️ costs money per hour — destroy at day's end!
  npx cdk destroy Neo4j
"""

import aws_cdk as cdk

from stacks.neo4j_stack import Neo4jStack

app = cdk.App()

# the participants' office/VPN CIDR — override via context, never default to 0.0.0.0/0
allowed_cidr = app.node.try_get_context("allowed_cidr") or "203.0.113.0/24"

Neo4jStack(app, "Neo4j", allowed_cidr=allowed_cidr)

cdk.Tags.of(app).add("project", "ai-ready-training")
cdk.Tags.of(app).add("owner", "participant")
app.synth()
