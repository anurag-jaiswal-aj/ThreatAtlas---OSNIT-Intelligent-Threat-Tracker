import pytest
import io
import uuid
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.schemas.event import EventResponse
from app.schemas.common import GeoJSONPoint
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_events():
    now = datetime.now(timezone.utc)
    return [
        EventResponse(
            id="64f9b8c3d91234567890abcd",
            title="Airstrike confirmed in capital",
            summary="Multiple sources confirmed a kinetic airstrike.",
            event_timestamp=now,
            created_at=now,
            updated_at=now,
            threat_level="High",
            threat_score=85.0,
            credibility_score=90.0,
            event_type="kinetic",
            country_code="ua",
            location_name="Kyiv",
            location=GeoJSONPoint(coordinates=[30.5234, 50.4501])
        ),
        EventResponse(
            id="64f9b8c3d91234567890abce",
            title="Civilian protest",
            summary="Peaceful gathering.",
            event_timestamp=now,
            created_at=now,
            updated_at=now,
            threat_level="Low",
            threat_score=10.0,
            credibility_score=60.0
        )
    ]

def test_export_pdf_returns_pdf(client, mocker, test_events):
    """1. Verify PDF export returns correct content type and signature."""
    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=test_events)
    response = client.get("/api/v1/events/export?format=pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "threatatlas_export.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")

def test_export_pdf_escaping_regression(client, mocker, test_events):
    """Regression test: Verify PDF generation succeeds with problematic XML characters."""
    test_events[0].title = "Bridge <damaged> & evacuation"
    test_events[0].summary = "Attack caused <major> damage & disrupted infrastructure."
    test_events[0].event_type = "kinetic <event>"

    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=[test_events[0]])

    response = client.get("/api/v1/events/export?format=pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_export_stix_returns_valid_bundle(client, mocker, test_events):
    """2. Verify STIX export returns valid STIX 2.1 JSON parsable by stix2."""
    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=test_events)
    response = client.get("/api/v1/events/export?format=stix")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/stix+json"
    assert "threatatlas_export.json" in response.headers["content-disposition"]

    from stix2 import parse
    bundle = parse(response.content, allow_custom=True)
    assert bundle.type == "bundle"
    assert len(bundle.objects) == 2
    assert bundle.objects[0].type == "incident"

def test_export_field_mapping(client, mocker, test_events):
    """3. Verify STIX fields map correctly and deterministic UUIDs are generated."""
    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=[test_events[0]])
    response = client.get("/api/v1/events/export?format=stix")

    data = response.json()
    incident = data["objects"][0]

    assert incident["name"] == "Airstrike confirmed in capital"
    assert incident["description"] == "Multiple sources confirmed a kinetic airstrike."
    assert "x_threatatlas_score" in incident
    assert incident["x_threatatlas_score"] == 85.0
    assert incident["x_threatatlas_country"] == "ua"
    assert incident["x_threatatlas_location"]["lon"] == 30.5234

    expected_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, "64f9b8c3d91234567890abcd"))
    assert incident["id"] == f"incident--{expected_uuid}"

def test_export_filters_respected(client, mocker):
    """4. Verify export passes filters to repository query."""
    mocker.patch("app.api.v1.endpoints.events.get_database")
    list_spy = mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=[])

    response = client.get("/api/v1/events/export?format=pdf&threat_level=High&countries=ua,ru&min_threat_score=50")
    assert response.status_code == 200

    list_spy.assert_called_once()
    _, kwargs = list_spy.call_args
    assert kwargs["threat_level"] == "High"
    assert set(kwargs["countries"]) == {"ua", "ru"}
    assert kwargs["min_threat_score"] == 50.0

def test_export_invalid_format(client):
    """5. Verify invalid format returns 400."""
    response = client.get("/api/v1/events/export?format=csv")
    assert response.status_code == 400
    assert "Unsupported export format" in response.text

def test_export_empty_result(client, mocker):
    """6. Verify empty result exports correctly without crashing."""
    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=[])

    pdf_res = client.get("/api/v1/events/export?format=pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF-")

    stix_res = client.get("/api/v1/events/export?format=stix")
    assert stix_res.status_code == 200
    data = stix_res.json()
    assert len(data.get("objects", [])) == 0

def test_export_no_internal_fields(client, mocker, test_events):
    """7. Verify MongoDB internal fields (like raw_post_ids) aren't leaked in STIX."""
    test_events[0].raw_post_ids = ["64f9b8c3d91234567890abcd"]
    mocker.patch("app.api.v1.endpoints.events.get_database")
    mocker.patch("app.db.repositories.event.EventRepository.list_events", return_value=[test_events[0]])

    response = client.get("/api/v1/events/export?format=stix")
    data = response.json()
    incident = data["objects"][0]

    assert "raw_post_ids" not in incident
    json_str = json.dumps(incident)
    assert "64f9b8c3d91234567890abcd" not in json_str  # ID shouldn't be exposed raw, only as UUIDv5
