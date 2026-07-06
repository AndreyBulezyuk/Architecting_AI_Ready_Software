"""First Bedrock call via the Converse API.

Usage:
    export BEDROCK_MODEL_ID=$(aws bedrock list-inference-profiles --region eu-west-1 \
        --query 'inferenceProfileSummaries[0].inferenceProfileId' --output text)
    uv run python bedrock_hello.py "Was ist eine Dead-Letter-Queue?"
"""

# boto3.client() exposes partially-untyped members; the result is annotated instead
# pyright: reportUnknownMemberType=false

import os
import sys
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


def main() -> None:
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        sys.exit("Set BEDROCK_MODEL_ID (see module docstring) — model ids are config, not code.")

    question = sys.argv[1] if len(sys.argv) > 1 else "Erkläre in einem Satz, was ein Event ist."

    bedrock: "BedrockRuntimeClient" = boto3.client("bedrock-runtime", region_name="eu-west-1")
    response = bedrock.converse(
        modelId=model_id,
        system=[{"text": "Antworte kurz, auf Deutsch."}],
        messages=[{"role": "user", "content": [{"text": question}]}],
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
