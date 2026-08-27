from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database
from pydantic import ValidationError

from app.schemas.webhook import WebhookAlertCreate, WebhookAlertResponse, WebhookAlertUpdate


class WebhookRepository:
    def __init__(self, db: Database):
        self.collection: Collection = db["webhooks"]

    async def get_by_id(self, webhook_id: str) -> Optional[WebhookAlertResponse]:
        if not ObjectId.is_valid(webhook_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(webhook_id)})
        if doc:
            return WebhookAlertResponse(**doc)
        return None

    async def list_webhooks(self, active_only: bool = False) -> List[WebhookAlertResponse]:
        query = {}
        if active_only:
            query["is_active"] = True
        
        cursor = self.collection.find(query).sort("created_at", -1)
        docs = await cursor.to_list(length=1000)
        return [WebhookAlertResponse(**doc) for doc in docs]

    async def create(self, webhook_in: WebhookAlertCreate) -> WebhookAlertResponse:
        doc = webhook_in.model_dump()
        now = datetime.now(timezone.utc)
        doc["created_at"] = now
        doc["updated_at"] = now

        result = await self.collection.insert_one(doc)
        created_doc = await self.collection.find_one({"_id": result.inserted_id})
        return WebhookAlertResponse(**created_doc)

    async def update(self, webhook_id: str, webhook_in: WebhookAlertUpdate) -> Optional[WebhookAlertResponse]:
        if not ObjectId.is_valid(webhook_id):
            return None

        update_data = {k: v for k, v in webhook_in.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_by_id(webhook_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.update_one(
            {"_id": ObjectId(webhook_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return None

        return await self.get_by_id(webhook_id)

    async def delete(self, webhook_id: str) -> bool:
        if not ObjectId.is_valid(webhook_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(webhook_id)})
        return result.deleted_count > 0
