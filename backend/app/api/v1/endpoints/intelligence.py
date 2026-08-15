import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, status
from app.db.session import get_database
from app.db.repositories.event import EventRepository
from app.db.repositories.raw_post import RawPostRepository
from app.nlp.service import nlp_service
from app.intelligence.service import intelligence_service

logger = logging.getLogger("threat_atlas.api.intelligence")

router = APIRouter()


class ProcessPendingResponse(BaseModel):
    processed_count: int = Field(..., description="Number of raw posts processed")
    events_created: int = Field(..., description="Number of new events created")
    events_merged: int = Field(..., description="Number of posts merged into existing events")
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
    raw_post_repo = RawPostRepository(db)
    event_repo = EventRepository(db)

    pending_posts = await raw_post_repo.list_pending(limit=limit)
    if not pending_posts:
        return ProcessPendingResponse(
            processed_count=0,
            events_created=0,
            events_merged=0,
            errors=0,
        )

    processed_count = 0
    events_created = 0
    events_merged = 0
    errors = 0

    for post in pending_posts:
        try:
            nlp_result = await nlp_service.process_text(post.text)
            result = await intelligence_service.process_post(
                raw_post=post,
                event_repo=event_repo,
                nlp_result=nlp_result,
                raw_post_repo=raw_post_repo,
            )

            processed_count += 1
            if result.get("action") == "created":
                events_created += 1
            elif result.get("action") == "merged":
                events_merged += 1

        except Exception as exc:
            logger.error("Error processing RawPost %s: %s", post.id, exc, exc_info=True)
            errors += 1
            await raw_post_repo.update_status(post.id, "failed")

    return ProcessPendingResponse(
        processed_count=processed_count,
        events_created=events_created,
        events_merged=events_merged,
        errors=errors,
    )
