import aws_cdk as cdk

from participant_stack import ParticipantStack

app = cdk.App()
ParticipantStack(app, "Participant")
cdk.Tags.of(app).add("project", "ai-ready-training")
cdk.Tags.of(app).add("owner", "participant")
app.synth()
