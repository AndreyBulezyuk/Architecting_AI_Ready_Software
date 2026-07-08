"""Read API, staged exactly like the exercise:

Etappe B: aggregate over raw signals (signal_count, last_seen_at) — works BEFORE
          any LLM ever ran; interests stay empty.
Etappe C/D: once the worker summarized a profile, the same endpoint additionally
          serves interests, persona_summary, travel_style and recommendations.

No LLM call in this path (resilience!).  Run: uv run fastapi dev api.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import dynamodb_client, settings

app = FastAPI(title="TravelMate User Profiles (exercise solution)")


class ProfileResponse(BaseModel):
    user_id: str
    signal_count: int
    last_seen_at: str
    # empty until the first condensation ran (Etappe B contract)
    interests: list[str] = Field(default_factory=list)
    persona_summary: str | None = None
    travel_style: str | None = None
    recommendations: list[str] = Field(default_factory=list)


@app.get("/user_profiles/{user_id}")
def get_profile(user_id: str) -> ProfileResponse:
    dynamodb = dynamodb_client()

    signals = dynamodb.query(
        TableName=settings.signals_table,
        KeyConditionExpression="user_id = :u",
        ExpressionAttributeValues={":u": {"S": user_id}},
    ).get("Items", [])
    if not signals:
        # 404, not an empty 200: "we know nothing about this user" is a fact
        # the caller must be able to distinguish from "user without profile yet"
        raise HTTPException(status_code=404, detail="no signals for this user")

    response = ProfileResponse(
        user_id=user_id,
        signal_count=len(signals),
        last_seen_at=max(item["occurred_at"].get("S", "") for item in signals),
    )

    profile = dynamodb.get_item(
        TableName=settings.profiles_table, Key={"user_id": {"S": user_id}}
    ).get("Item")
    if profile is not None:  # Etappe C/D: the summarized view exists
        response.interests = [value.get("S", "") for value in profile["interests"].get("L", [])]
        response.persona_summary = profile["persona_summary"].get("S")
        response.travel_style = profile["travel_style"].get("S")
        response.recommendations = [
            value.get("S", "") for value in profile["recommendations"].get("L", [])
        ]
    return response
