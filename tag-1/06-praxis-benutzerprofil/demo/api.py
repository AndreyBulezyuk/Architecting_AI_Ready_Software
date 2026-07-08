"""Read API for the profile component — no LLM call in this path (resilience!).

Run: uv run fastapi dev api.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import dynamodb_client, settings

app = FastAPI(title="TravelMate User Profiles")


class ProfileResponse(BaseModel):
    user_id: str
    interests: list[str]
    persona_summary: str
    travel_style: str
    recommendations: list[str]
    updated_at: str


@app.get("/user_profiles/{user_id}")
def get_profile(user_id: str) -> ProfileResponse:
    item = dynamodb_client().get_item(
        TableName=settings.profiles_table, Key={"user_id": {"S": user_id}}
    ).get("Item")
    if item is None:
        # 404, not an empty 200: "no profile yet" is a fact the caller must see
        raise HTTPException(status_code=404, detail="no profile for this user yet")
    return ProfileResponse(
        user_id=user_id,
        interests=[value.get("S", "") for value in item["interests"].get("L", [])],
        persona_summary=item["persona_summary"].get("S", ""),
        travel_style=item["travel_style"].get("S", "unknown"),
        recommendations=[value.get("S", "") for value in item["recommendations"].get("L", [])],
        updated_at=item["updated_at"].get("S", ""),
    )
