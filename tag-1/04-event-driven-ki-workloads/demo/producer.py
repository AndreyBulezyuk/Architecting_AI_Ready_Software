"""Publish SearchSubmitted events to the bus.

Run: uv run python producer.py "hotel am meer" [user-id]
"""

import sys

from config import events_client, settings
from models import EVENT_SOURCE, SearchSubmitted


def publish(event: SearchSubmitted) -> None:
    response = events_client().put_events(
        Entries=[{
            "EventBusName": settings.bus_name,
            "Source": EVENT_SOURCE,
            "DetailType": SearchSubmitted.DETAIL_TYPE,
            "Detail": event.model_dump_json(),
        }]
    )
    if response["FailedEntryCount"] != 0:
        raise RuntimeError(f"publish failed: {response['Entries']}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "hotel am meer"
    user_id = sys.argv[2] if len(sys.argv) > 2 else "user-42"
    evt = SearchSubmitted(user_id=user_id, query=query)
    publish(evt)
    print(f"published {evt.event_id}: {query!r} for {user_id}")
