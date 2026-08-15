from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.session import get_database
from app.ingestion.service import IngestionService, IngestionStatistics

router = APIRouter(prefix="/ingestion", tags=["Ingestion (Development)"])


@router.post(
    "/rss",
    response_model=IngestionStatistics,
    status_code=200,
    summary="[Development] Manually trigger RSS OSINT ingestion",
    description=(
        "Development endpoint to manually trigger the public RSS feed ingestion pipeline. "
        "Fetches configured feeds, parses entries, normalizes raw posts, and saves non-duplicate "
        "items into MongoDB. NOTE: This endpoint is unauthenticated for development and will be "
        "secured in future authentication phases."
    ),
)
async def trigger_rss_ingestion(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> IngestionStatistics:
    """Trigger manual RSS feed ingestion and return statistics summary."""
    try:
        service = IngestionService(db)
        stats = await service.ingest_all_feeds()
        return stats
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing RSS ingestion: {str(exc)}",
        )
