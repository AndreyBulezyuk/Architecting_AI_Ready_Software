"""Event contracts — validated at every boundary (see theorie.md, slide 5)."""

from datetime import UTC, datetime
from typing import ClassVar, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

EVENT_SOURCE = "travelmate"


class SearchSubmitted(BaseModel):
    """A user submitted a search — thin event: ids and the query, no fat payload."""

    DETAIL_TYPE: ClassVar[str] = "SearchSubmitted"

    event_version: Literal["1"] = "1"
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str
    query: str
