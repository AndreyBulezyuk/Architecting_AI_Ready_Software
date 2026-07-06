"""Event contract for the exercise (conventions from chapter 04)."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentUpdated(BaseModel):
    event_version: Literal["1"] = "1"
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_id: str
