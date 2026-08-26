from unittest.mock import AsyncMock, MagicMock
import pytest
from bson import ObjectId
from app.db.repositories.event import EventRepository
from app.db.repositories.raw_post import RawPostRepository
from app.schemas.common import GeoJSONPoint, utc_now
from app.schemas.event import EventCreate
from app.schemas.raw_post import RawPostCreate


@pytest.mark.asyncio
async def test_raw_post_repository_create():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    fake_id = ObjectId()
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))

    repo = RawPostRepository(mock_db)
    post_in = RawPostCreate(
        source="telegram",
        source_specific_id="101",
        text="Sample post text",
        original_timestamp=utc_now(),
    )

    result = await repo.create(post_in)
    assert result is not None
    assert result.id == str(fake_id)
    assert result.source == "telegram"
    mock_collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_raw_post_repository_get_by_id():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    fake_id = ObjectId()
    now = utc_now()
    fake_doc = {
        "_id": fake_id,
        "source": "rss",
        "source_specific_id": "guid-999",
        "text": "RSS feed content",
        "original_timestamp": now,
        "collected_at": now,
        "processing_status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    mock_collection.find_one = AsyncMock(return_value=fake_doc)

    repo = RawPostRepository(mock_db)
    result = await repo.get_by_id(str(fake_id))
    assert result is not None
    assert result.id == str(fake_id)
    assert result.source_specific_id == "guid-999"


@pytest.mark.asyncio
async def test_event_repository_create():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    fake_id = ObjectId()
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))

    repo = EventRepository(mock_db)
    event_in = EventCreate(
        title="Test Event",
        event_timestamp=utc_now(),
        location=GeoJSONPoint(type="Point", coordinates=[10.0, 50.0]),
        threat_level="Medium",
    )

    result = await repo.create(event_in)
    assert result is not None
    assert result.id == str(fake_id)
    assert result.title == "Test Event"
    assert result.threat_level == "Medium"


@pytest.mark.asyncio
async def test_event_repository_get_global_metrics():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[
        {"_id": "High", "count": 10},
        {"_id": "Medium", "count": 20},
        {"_id": "Low", "count": 30},
        {"_id": "Unknown", "count": 5}, # Test that we capture unexpected levels in total
    ])
    mock_collection.aggregate.return_value = mock_cursor

    repo = EventRepository(mock_db)
    metrics = await repo.get_global_metrics()

    assert metrics.high == 10
    assert metrics.medium == 20
    assert metrics.low == 30
    assert metrics.total == 65

    mock_collection.aggregate.assert_called_once()
