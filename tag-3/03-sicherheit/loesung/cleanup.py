"""Delete the demo guardrail (the only AWS resource this chapter creates).

Run: uv run python cleanup.py
"""

from config import bedrock_client, settings


def main() -> None:
    bedrock = bedrock_client()
    for summary in bedrock.list_guardrails().get("guardrails", []):
        if summary.get("name") == settings.guardrail_name:
            guardrail_id = summary.get("id")
            assert guardrail_id is not None
            bedrock.delete_guardrail(guardrailIdentifier=guardrail_id)
            print(f"deleted guardrail {settings.guardrail_name} ({guardrail_id})")
            return
    print("no guardrail to delete")


if __name__ == "__main__":
    main()
