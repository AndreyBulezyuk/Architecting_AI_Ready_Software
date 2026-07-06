"""Event contracts for the exercise: the new BookingCreated event."""

from datetime import UTC, datetime
from typing import ClassVar, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

EVENT_SOURCE = "travelmate"


class BookingCreated(BaseModel):
    DETAIL_TYPE: ClassVar[str] = "BookingCreated"

    event_version: Literal["1"] = "1"
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str
    destination: str
    price_eur: float
