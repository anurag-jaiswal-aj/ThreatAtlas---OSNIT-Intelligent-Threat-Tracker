from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.webhook import WebhookAlertCreate, WebhookAlertUpdate, WebhookAlertResponse
from app.db.repositories.webhook import WebhookRepository
from app.db.session import get_database
from app.services.webhook_service import validate_webhook_url, SecurityValidationError

router = APIRouter()

@router.post("", response_model=WebhookAlertResponse, status_code=status.HTTP_201_CREATED, summary="Create Webhook")
async def create_webhook(webhook_in: WebhookAlertCreate):
    try:
        validate_webhook_url(webhook_in.url)
    except SecurityValidationError as e:
        # Don't leak the exact resolved IP in error message to prevent probing, just give the exception string.
        raise HTTPException(status_code=400, detail=str(e))
        
    db = get_database()
    repo = WebhookRepository(db)
    return await repo.create(webhook_in)

@router.get("", response_model=List[WebhookAlertResponse], summary="List Webhooks")
async def list_webhooks():
    db = get_database()
    repo = WebhookRepository(db)
    return await repo.list_webhooks()

@router.patch("/{id}", response_model=WebhookAlertResponse, summary="Update Webhook")
async def update_webhook(id: str, webhook_in: WebhookAlertUpdate):
    if webhook_in.url is not None:
        try:
            validate_webhook_url(webhook_in.url)
        except SecurityValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    db = get_database()
    repo = WebhookRepository(db)
    updated = await repo.update(id, webhook_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Webhook")
async def delete_webhook(id: str):
    db = get_database()
    repo = WebhookRepository(db)
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")

@router.post("/{id}/test", summary="Test Webhook")
async def test_webhook(id: str):
    db = get_database()
    repo = WebhookRepository(db)
    webhook = await repo.get_by_id(id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    from datetime import datetime, timezone
    from app.schemas.event import EventResponse
    from app.services.webhook_service import dispatch_webhook
    
    # Create a safe fake event
    test_event = EventResponse(
        id="000000000000000000000000",
        title="Test Threat Event",
        summary="This is a test event to verify webhook delivery.",
        raw_post_ids=[],
        source_ids=[],
        threat_level="High",
        threat_score=100.0,
        credibility_score=100.0,
        event_type="test",
        event_timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    success = await dispatch_webhook(webhook, test_event)
    if not success:
        raise HTTPException(status_code=500, detail="Webhook delivery failed. Check URL and server status.")
    return {"status": "success", "detail": "Test payload delivered."}
