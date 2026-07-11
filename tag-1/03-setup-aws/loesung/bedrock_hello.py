"""First Bedrock call via the Converse API.

Usage:
    uv run python bedrock_hello.py "Was ist eine Dead-Letter-Queue?"

No model access request, Marketplace subscription, CDK, or extra CLI step is needed:
Google Gemma on Bedrock is pay-per-token — you are billed only for the tokens of
this one call (~250 tokens ≈ a fraction of a cent), nothing while idle.

Where does the model id come from? It is a simple foundation-model id — no cross-region
inference profile prefix is needed for Gemma 4. List the available models for the
account and pick one:
    aws bedrock list-inference-profiles --profile default --region eu-west-1 \
        --query "inferenceProfileSummaries[?contains(inferenceProfileId, 'nova')].inferenceProfileId" \
        --output text

The model id `eu.amazon.nova-lite-v1:0` is a standard on-demand Bedrock model id.
Override the default below via BEDROCK_MODEL_ID.
"""

# boto3.client() exposes partially-untyped members; the result is annotated instead
# pyright: reportUnknownMemberType=false

import os
import sys
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


DEFAULT_MODEL_ID = "eu.amazon.nova-lite-v1:0"


def main() -> None:
    # Cheap Gemma model; override via env for other models.
    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    # Show which model is in play — a stale exported BEDROCK_MODEL_ID (e.g. a legacy id
    # from an earlier attempt) silently overrides the default; print it so that's visible.
    source = "BEDROCK_MODEL_ID env" if "BEDROCK_MODEL_ID" in os.environ else "default"
    print(f"[model: {model_id} (from {source})]", file=sys.stderr)

    question = sys.argv[1] if len(sys.argv) > 1 else "Erkläre in einem Satz, was ein Event ist."

    # Bind to the training profile so credentials resolve without exporting AWS_PROFILE.
    # The profile uses the `aws login` credential provider (login_session in ~/.aws/config),
    # which requires the CRT extra — see botocore[crt] in pyproject.toml.
    profile = os.environ.get("AWS_PROFILE", "default")
    session = boto3.Session(profile_name=profile, region_name="eu-west-1")
    bedrock: "BedrockRuntimeClient" = session.client("bedrock-runtime")
    try:
        response = bedrock.converse(
            modelId=model_id,
            system=[{"text": "Antworte kurz, auf Deutsch."}],
            messages=[{"role": "user", "content": [{"text": question}]}],
        )
    except bedrock.exceptions.ResourceNotFoundException:
        sys.exit(
            f"Model '{model_id}' is not usable (legacy or not available in eu-west-1). "
            f"Unset BEDROCK_MODEL_ID to use the default '{DEFAULT_MODEL_ID}', "
            "or pick an active one:\n"
            "  aws bedrock list-inference-profiles --profile default --region eu-west-1 "
            "--query \"inferenceProfileSummaries[?contains(inferenceProfileId, 'nova')]"
            '.inferenceProfileId"'
        )

    # response fields are optional in the API contract — access them defensively
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    answer = (message.get("content") or [{}])[0].get("text", "<no text>")
    usage = response["usage"]
    print(answer)
    print(
        f"\n--- tokens: in={usage['inputTokens']} out={usage['outputTokens']} "
        f"total={usage['totalTokens']}"
    )


if __name__ == "__main__":
    main()
