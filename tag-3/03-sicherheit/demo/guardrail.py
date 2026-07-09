"""Create (or find) a Bedrock guardrail for the TravelMate assistant.

All three policies below are verified to work in eu-west-1 (July 2026):
  - topic policy: refuse investment advice (off-domain for a travel assistant)
  - content policy: PROMPT_ATTACK filter (jailbreak / prompt-injection defence)
  - sensitive-information policy: anonymize emails, block card numbers

Run: uv run python guardrail.py   (prints the guardrail id)

Note: no CDK L2 construct exists for guardrails (only the L1 CfnGuardrail) — for a
one-resource, throwaway training setup we create it via boto3, exactly like the
SQS/DynamoDB setup in tag-1/04. In production it would live in the CDK app.
"""

import time

from config import bedrock_client, settings


def _wait_ready(guardrail_id: str, attempts: int = 30) -> None:
    """No boto3 waiter exists for guardrails — poll the status ourselves."""
    bedrock = bedrock_client()
    for _ in range(attempts):
        status = bedrock.get_guardrail(guardrailIdentifier=guardrail_id).get("status")
        if status == "READY":
            return
        if status == "FAILED":
            raise RuntimeError(f"guardrail {guardrail_id} entered FAILED state")
        time.sleep(1)
    raise TimeoutError(f"guardrail {guardrail_id} not READY after {attempts}s")


def ensure_guardrail() -> str:
    """create-if-missing; returns the guardrail id."""
    bedrock = bedrock_client()
    for summary in bedrock.list_guardrails().get("guardrails", []):
        if summary.get("name") == settings.guardrail_name:
            guardrail_id = summary.get("id")
            assert guardrail_id is not None
            return guardrail_id

    response = bedrock.create_guardrail(
        name=settings.guardrail_name,
        blockedInputMessaging="Diese Anfrage wurde von einer Sicherheitsrichtlinie blockiert.",
        blockedOutputsMessaging="Diese Antwort wurde von einer Sicherheitsrichtlinie blockiert.",
        topicPolicyConfig={
            "topicsConfig": [{
                "name": "Anlageberatung",
                "definition": (
                    "Empfehlungen zum Kauf oder Verkauf von Finanzprodukten, "
                    "Aktien oder Kryptowaehrungen."
                ),
                "examples": ["Welche Aktie soll ich kaufen?"],
                "type": "DENY",
            }]
        },
        contentPolicyConfig={
            "filtersConfig": [
                # PROMPT_ATTACK only supports strength on the INPUT side (output must be NONE)
                {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
            ]
        },
        sensitiveInformationPolicyConfig={
            "piiEntitiesConfig": [
                {"type": "EMAIL", "action": "ANONYMIZE"},
                {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
            ]
        },
    )
    guardrail_id = response["guardrailId"]
    _wait_ready(guardrail_id)
    return guardrail_id


if __name__ == "__main__":
    print(f"guardrail id: {ensure_guardrail()}")
