"""Own guardrail for the exercise: medical-advice topic + prompt-attack + PII.

Different denied topic than the demo (medical instead of investment advice) so
you actually design the policy rather than copy it.
"""

import time

from config import bedrock_client, settings


def _wait_ready(guardrail_id: str, attempts: int = 30) -> None:
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
                "name": "Medizinische Beratung",
                "definition": (
                    "Diagnosen, Behandlungsempfehlungen oder Medikamenten-Dosierungen."
                ),
                "examples": ["Welches Medikament soll ich gegen Kopfschmerzen nehmen?"],
                "type": "DENY",
            }]
        },
        contentPolicyConfig={
            "filtersConfig": [
                {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
            ]
        },
        sensitiveInformationPolicyConfig={
            "piiEntitiesConfig": [{"type": "EMAIL", "action": "ANONYMIZE"}]
        },
    )
    guardrail_id = response["guardrailId"]
    _wait_ready(guardrail_id)
    return guardrail_id


if __name__ == "__main__":
    print(f"guardrail id: {ensure_guardrail()}")
