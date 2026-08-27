import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, status
from app.db.session import get_database
from app.db.repositories.event import EventRepository
from app.db.repositories.raw_post import RawPostRepository
from app.nlp.service import nlp_service
from app.intelligence.service import intelligence_service
from app.intelligence.threat_scorer import is_post_relevant

logger = logging.getLogger("threat_atlas.api.intelligence")

router = APIRouter()


class ProcessPendingResponse(BaseModel):
    processed_count: int = Field(..., description="Number of raw posts processed")
    events_created: int = Field(..., description="Number of new events created")
    events_merged: int = Field(..., description="Number of posts merged into existing events")
    events_ignored: int = Field(..., description="Number of posts ignored because they were not threat-relevant")
    errors: int = Field(..., description="Number of posts that failed during processing")


@router.post("/process-pending", response_model=ProcessPendingResponse, status_code=status.HTTP_200_OK, summary="Trigger Batch NLP & Intelligence Processing")
async def process_pending_posts(limit: int = 100):
    """
    Executes the end-to-end processing pipeline on all pending RawPosts:
    1. Fetches RawPosts with processing_status == 'pending'.
    2. Runs text cleaning, NER, EntityRuler, and Geocoding via NLPService.
    3. Runs Threat Scoring, Credibility Scoring, and Event Clustering via IntelligenceService.
    4. Updates RawPost status to 'processed'.
    5. Returns statistics on processed posts and generated/merged events.
    """
    db = get_database()
    stats = await intelligence_service.process_pending_batch(db=db, limit=limit)
    return ProcessPendingResponse(**stats)
