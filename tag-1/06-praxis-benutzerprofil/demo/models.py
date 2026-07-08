"""Event contracts (chapter 04 conventions) and the LLM output contract."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SearchSubmitted(BaseModel):
    event_version: Literal["1"] = "1"
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str
    query: str


class BookingCreated(BaseModel):
    event_version: Literal["1"] = "1"
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str
    destination: str
    price_eur: float


class ProfileSummary(BaseModel):
    """Contract for the LLM condensation — validated, never trusted blindly."""

    interests: list[str] = Field(max_length=5)
    persona_summary: str = Field(max_length=300)
    travel_style: Literal["budget", "comfort", "luxury", "unknown"]
