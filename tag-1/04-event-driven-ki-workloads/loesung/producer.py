"""Publish BookingCreated events (optionally the same event twice for the dedup test)."""

from config import events_client, settings
from models import EVENT_SOURCE, BookingCreated


def publish(event: BookingCreated) -> None:
    response = events_client().put_events(
        Entries=[{
            "EventBusName": settings.bus_name,
            "Source": EVENT_SOURCE,
            "DetailType": BookingCreated.DETAIL_TYPE,
            "Detail": event.model_dump_json(),
        }]
    )
    if response["FailedEntryCount"] != 0:
        raise RuntimeError(f"publish failed: {response['Entries']}")


if __name__ == "__main__":
    evt = BookingCreated(user_id="user-46", destination="Lisbon", price_eur=499.0)
    publish(evt)
    publish(evt)  # same event_id twice -> worker must process it exactly once
    print(f"published {evt.event_id} twice")
