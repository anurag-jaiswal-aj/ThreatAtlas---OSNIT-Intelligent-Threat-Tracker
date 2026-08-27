from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.common import GeoJSONPoint, utc_now
from app.schemas.event import EventCreate, EventResponse
from app.schemas.raw_post import RawPostCreate, RawPostResponse


def test_raw_post_create_valid():
    now = utc_now()
    post_data = {
        "source": "telegram",
        "source_specific_id": "msg_12345",
        "text": "Reported explosions near Kharkiv city center.",
        "url": "https://t.me/example/12345",
        "original_timestamp": now,
        "language": "en",
        "author": "analyst_1",
    }
    post = RawPostCreate(**post_data)
    assert post.source == "telegram"
    assert post.source_specific_id == "msg_12345"
    assert post.processing_status == "pending"
    assert post.original_timestamp.tzinfo is not None


def test_raw_post_invalid_missing_required():
    with pytest.raises(ValidationError) as exc_info:
        RawPostCreate(
            source="rss",
            # Missing source_specific_id, text, original_timestamp
        )
    errors = exc_info.value.errors()
    field_names = [e["loc"][0] for e in errors]
    assert "source_specific_id" in field_names
    assert "text" in field_names
    assert "original_timestamp" in field_names


def test_event_create_valid():
    now = utc_now()
    event_data = {
        "title": "Airstrike reported near Kharkiv airfield",
        "summary": "Multiple local sources report heavy smoke.",
        "raw_post_ids": ["60d5ec49f1b2c81128c70123"],
        "source_ids": ["telegram_channel_1"],
        "event_type": "airstrike",
        "entities": {
            "locations": ["Kharkiv"],
            "organizations": ["Air Force"],
            "equipment": ["Su-34"],
        },
        "location_name": "Kharkiv Airfield",
        "location": GeoJSONPoint(type="Point", coordinates=[36.25, 49.98]),
        "event_timestamp": now,
        "threat_score": 75.5,
        "threat_level": "High",
        "credibility_score": 80.0,
    }
    event = EventCreate(**event_data)
    assert event.title == "Airstrike reported near Kharkiv airfield"
    assert event.threat_level == "High"
    assert event.location.coordinates == [36.25, 49.98]


def test_event_invalid_threat_level():
    now = utc_now()
    with pytest.raises(ValidationError):
        EventCreate(
            title="Invalid event",
            event_timestamp=now,
            threat_level="Extreme",  # Invalid! Must be Low, Medium, or High
        )


def test_event_invalid_threat_score_range():
    now = utc_now()
    with pytest.raises(ValidationError):
        EventCreate(
            title="Out of bounds threat score",
            event_timestamp=now,
            threat_score=150.0,  # Invalid! ge=0.0, le=100.0
        )


def test_geojson_point_validation():
    point = GeoJSONPoint(coordinates=[30.5234, 50.4501])
    assert point.type == "Point"
    assert point.coordinates == [30.5234, 50.4501]

    with pytest.raises(ValidationError):
        GeoJSONPoint(coordinates=[30.5234])  # Invalid, requires 2 floats

def test_event_schema_country_code():
    from app.schemas.event import EventBase
    from datetime import datetime

    # Valid with country code
    evt1 = EventBase(title="Test", event_timestamp=datetime.now(), country_code="ua")
    assert evt1.country_code == "ua"

    # Valid without country code
    evt2 = EventBase(title="Test", event_timestamp=datetime.now())
    assert evt2.country_code is None
