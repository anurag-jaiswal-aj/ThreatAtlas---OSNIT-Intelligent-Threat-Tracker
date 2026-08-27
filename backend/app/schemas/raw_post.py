from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.common import PyObjectId, ensure_utc, utc_now


class RawPostBase(BaseModel):
    source: str = Field(..., description="Public OSINT source name (e.g., 'telegram', 'rss')")
    source_specific_id: str = Field(..., description="Unique ID provided by the origin source")
    text: str = Field(..., description="Raw text content collected")
    url: Optional[str] = Field(None, description="Original URL of the post if available")
    original_timestamp: datetime = Field(..., description="Timestamp of post publish at origin (UTC)")
    language: Optional[str] = Field(None, description="ISO language code if detected")
    author: Optional[str] = Field(None, description="Author identifier or username")
    media_metadata: Optional[Dict[str, Any]] = Field(None, description="Image/video attachments metadata")

    @field_validator("original_timestamp", mode="before")
    @classmethod
    def validate_utc(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v


class RawPostCreate(RawPostBase):
    collected_at: datetime = Field(default_factory=utc_now)
    processing_status: str = Field(default="pending", description="Processing status: pending, processed, failed, duplicate, ignored")

    @field_validator("collected_at", mode="before")
    @classmethod
    def validate_collected_utc(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v


class RawPostUpdate(BaseModel):
    processing_status: Optional[str] = None
    language: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=utc_now)


class RawPostInDB(RawPostBase):
    id: Annotated[ObjectId, PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    collected_at: datetime = Field(default_factory=utc_now)
    processing_status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class RawPostResponse(RawPostBase):
    id: str = Field(..., description="Database object ID as string")
    collected_at: datetime
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RawPostListResponse(BaseModel):
    total: int = Field(..., description="Total matching raw posts count")
    limit: int = Field(..., description="Page limit")
    skip: int = Field(..., description="Page skip offset")
    items: List[RawPostResponse] = Field(..., description="List of raw posts")

