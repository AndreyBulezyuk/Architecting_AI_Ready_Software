"""Wires Ragas' judge LLM to Bedrock via the `instructor` library.

Ragas 0.4's metric classes (ragas.metrics.collections) take an InstructorBaseRagasLLM,
not a raw provider client. There is no dedicated "bedrock" adapter in ragas itself —
this goes through instructor's own Bedrock support instead. Two things had to be
found by testing against a real Bedrock call, not just read from docs:

1. The LLM must be constructed as an ASYNC instructor client (`async_client=True`).
   Ragas metrics always call `.ascore()` internally; a sync-only instructor client
   raises "Cannot use agenerate() with a synchronous client."
2. Ragas' default InstructorModelArgs sends BOTH `temperature` and `top_p` to the
   model. Bedrock's Converse API rejects that combination for Claude with
   `ValidationException: temperature and top_p cannot both be specified`.
   Fix: delete `top_p` from the constructed LLM's model_args after the fact —
   InstructorModelArgs itself has no Optional[top_p], so it can't be set to None
   at construction time.
"""

import os

import boto3
import instructor
from ragas.llms.base import InstructorLLM

from config import settings


def bedrock_judge(model_id: str | None = None, max_tokens: int = 1024) -> InstructorLLM:
    profile = os.environ.get("AWS_PROFILE", "ai-training")
    session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
    boto_client = session.client("bedrock-runtime")  # pyright: ignore[reportUnknownMemberType]

    patched = instructor.from_bedrock(
        boto_client, model=model_id or settings.chat_model_id, async_client=True
    )
    llm = InstructorLLM(
        client=patched,
        model=model_id or settings.chat_model_id,
        provider="bedrock",
        temperature=0.0,
        max_tokens=max_tokens,
    )
    del llm.model_args["top_p"]  # pyright: ignore[reportUnknownMemberType]  (see module docstring, point 2)
    return llm
