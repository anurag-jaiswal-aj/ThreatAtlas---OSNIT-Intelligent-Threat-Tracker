from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient
from main import app
from app.schemas.common import GeoJSONPoint, utc_now
from app.schemas.event import EventResponse
from app.schemas.raw_post import RawPostResponse

client = TestClient(app)


def test_list_events_no_filters(mocker):
    """1. Test GET /api/v1/events with no filters (returns 200 and list)."""
    fake_id = str(ObjectId())
    now = datetime(2026, 8, 12, 12, 0, 0, tzinfo=timezone.utc)
    mock_event = EventResponse(
        id=fake_id,
        title="Test Security Event",
        summary="A test event",
        raw_post_ids=["p1"],
        source_ids=["bbc"],
        event_type="protest",
        entities={"locations": ["Paris"], "organizations": [], "equipment": []},
        location_name="Paris",
        location=GeoJSONPoint(coordinates=[2.35, 48.85]),
        event_timestamp=now,
        threat_score=45.0,
        threat_level="Medium",
        credibility_score=85.0,
        corroboration_count=1,
        created_at=now,
        updated_at=now,
    )

    mocker.patch("app.api.v1.endpoints.events.EventRepository.list_events", AsyncMock(return_value=[mock_event]))
    mocker.patch("app.api.v1.endpoints.events.EventRepository.count_events", AsyncMock(return_value=1))
    mocker.patch("app.api.v1.endpoints.events.get_database", return_value=MagicMock())

    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Security Event"
    assert data["items"][0]["threat_level"] == "Medium"


def test_filter_events_by_threat_level(mocker):
    """2. Test filtering events by threat_level (Low/Medium/High)."""
    fake_id = str(ObjectId())
    now = utc_now()
    mock_event = EventResponse(
        id=fake_id,
        title="High Threat Incident",
        event_timestamp=now,
        threat_score=85.0,
        threat_level="High",
        created_at=now,
        updated_at=now,
    )

    mocker.patch("app.api.v1.endpoints.events.EventRepository.list_events", AsyncMock(return_value=[mock_event]))
    mocker.patch("app.api.v1.endpoints.events.EventRepository.count_events", AsyncMock(return_value=1))
    mocker.patch("app.api.v1.endpoints.events.get_database", return_value=MagicMock())

    # Valid threat level High
    response = client.get("/api/v1/events?threat_level=High")
    assert response.status_code == 200
    assert response.json()["items"][0]["threat_level"] == "High"

    # Invalid threat level -> 400 Bad Request
    response_invalid = client.get("/api/v1/events?threat_level=Extreme")
    assert response_invalid.status_code == 400
    assert "Invalid threat_level" in response_invalid.json()["detail"]


def test_bbox_parsing_valid_vs_invalid(mocker):
    """3. Test bbox parsing with valid coordinates vs invalid string format (400 response)."""
    mocker.patch("app.api.v1.endpoints.events.EventRepository.list_events", AsyncMock(return_value=[]))
    mocker.patch("app.api.v1.endpoints.events.EventRepository.count_events", AsyncMock(return_value=0))
    mocker.patch("app.api.v1.endpoints.events.get_database", return_value=MagicMock())

    # Valid bbox: min_lon,min_lat,max_lon,max_lat
    res_valid = client.get("/api/v1/events?bbox=2.0,48.0,3.0,49.0")
    assert res_valid.status_code == 200

    # Malformed bbox string -> 400
    res_malformed = client.get("/api/v1/events?bbox=2.0,48.0,invalid")
    assert res_malformed.status_code == 400
    assert "Invalid bbox" in res_malformed.json()["detail"]

    # min > max bbox -> 400
    res_inverted = client.get("/api/v1/events?bbox=10.0,48.0,2.0,49.0")
    assert res_inverted.status_code == 400


def test_get_single_event_valid_vs_nonexistent(mocker):
    """4. Test GET /api/v1/events/{id} with valid vs non-existent ID (404 response)."""
    fake_id = str(ObjectId())
    now = utc_now()
    mock_event = EventResponse(
        id=fake_id,
        title="Single Event",
        event_timestamp=now,
        threat_score=30.0,
        threat_level="Low",
        created_at=now,
        updated_at=now,
    )

    mocker.patch("app.api.v1.endpoints.events.get_database", return_value=MagicMock())

    # Found event
    mocker.patch("app.api.v1.endpoints.events.EventRepository.get_by_id", AsyncMock(return_value=mock_event))
    res_found = client.get(f"/api/v1/events/{fake_id}")
    assert res_found.status_code == 200
    assert res_found.json()["id"] == fake_id

    # Non-existent ID -> 404
    non_existent_id = str(ObjectId())
    mocker.patch("app.api.v1.endpoints.events.EventRepository.get_by_id", AsyncMock(return_value=None))
    res_missing = client.get(f"/api/v1/events/{non_existent_id}")
    assert res_missing.status_code == 404
    assert "not found" in res_missing.json()["detail"]

    # Invalid ObjectId hex string -> 400
    res_invalid_id = client.get("/api/v1/events/invalid-hex-id")
    assert res_invalid_id.status_code == 400


def test_process_pending_intelligence_flow(mocker):
    """5. Test POST /api/v1/intelligence/process-pending processing flow."""
    now = utc_now()
    post_id = str(ObjectId())
    pending_post = RawPostResponse(
        id=post_id,
        source="bbc",
        source_specific_id="guid-101",
        text="Airstrike reported near Kyiv with drone activity.",
        original_timestamp=now,
        collected_at=now,
        processing_status="pending",
        created_at=now,
        updated_at=now,
    )

    mocker.patch("app.api.v1.endpoints.intelligence.get_database", return_value=MagicMock())
    mocker.patch("app.api.v1.endpoints.intelligence.RawPostRepository.list_pending", AsyncMock(return_value=[pending_post]))
    mocker.patch("app.api.v1.endpoints.intelligence.RawPostRepository.update_status", AsyncMock(return_value=True))

    mock_nlp_result = MagicMock()
    mocker.patch("app.api.v1.endpoints.intelligence.nlp_service.process_text", AsyncMock(return_value=mock_nlp_result))
    mocker.patch(
        "app.api.v1.endpoints.intelligence.intelligence_service.process_post",
        AsyncMock(return_value={"action": "created", "event_id": str(ObjectId())}),
    )

    response = client.post("/api/v1/intelligence/process-pending")
    assert response.status_code == 200
    data = response.json()
    assert data["processed_count"] == 1
    assert data["events_created"] == 1
    assert data["events_merged"] == 0
    assert data["errors"] == 0
