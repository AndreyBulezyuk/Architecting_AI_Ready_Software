"""Publish a small mixed event stream for one user (incl. one duplicate).

Run: uv run python simulate_user.py user-42
"""

import sys

from config import events_client, settings
from models import BookingCreated, SearchSubmitted
from pydantic import BaseModel


def publish(event: BaseModel) -> None:
    events_client().put_events(
        Entries=[{
            "EventBusName": settings.bus_name,
            "Source": "travelmate",
            "DetailType": type(event).__name__,
            "Detail": event.model_dump_json(),
        }]
    )


def simulate(user_id: str) -> int:
    events: list[BaseModel] = [
        SearchSubmitted(user_id=user_id, query="strand mit kindern"),
        SearchSubmitted(user_id=user_id, query="familienhotel am meer"),
        SearchSubmitted(user_id=user_id, query="flache bucht zum baden"),
        BookingCreated(user_id=user_id, destination="Algarve", price_eur=1450.0),
        SearchSubmitted(user_id=user_id, query="sandburg strand portugal"),
    ]
    events.append(events[0])  # duplicate on purpose — the worker must dedup it
    for event in events:
        publish(event)
    return len(events)


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "user-42"
    print(f"published {simulate(user)} events (1 duplicate) for {user}")
