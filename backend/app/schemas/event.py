from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.common import GeoJSONPoint, PyObjectId, ensure_utc, utc_now


def default_entities() -> Dict[str, List[str]]:
    return {"locations": [], "organizations": [], "equipment": []}


class EventBase(BaseModel):
    title: str = Field(..., description="Short descriptive title of the intelligence event")
    summary: Optional[str] = Field(None, description="Detailed summary generated or extracted")
    raw_post_ids: List[str] = Field(default_factory=list, description="IDs of corroborating raw posts")
    source_ids: List[str] = Field(default_factory=list, description="Unique source identifiers contributing to event")
    event_type: Optional[str] = Field(None, description="Categorized event type (e.g., 'airstrike', 'protest')")
    entities: Dict[str, List[str]] = Field(default_factory=default_entities, description="Extracted named entities")
    location_name: Optional[str] = Field(None, description="Human-readable location name")
    location: Optional[GeoJSONPoint] = Field(None, description="GeoJSON point coordinates [lng, lat]")
    country_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 country code")
    event_timestamp: datetime = Field(..., description="Primary timestamp when the event occurred (UTC)")
    threat_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Calculated threat score (0-100)")
    threat_level: str = Field(default="Low", description="Threat category: Low, Medium, High")
    credibility_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Source credibility score (0-100)")
    related_event_ids: List[str] = Field(default_factory=list, description="IDs of linked or related events")
    corroboration_count: int = Field(default=1, ge=1, description="Number of distinct corroborating reports")
    score_breakdown: Optional[Dict[str, Any]] = Field(None, description="Transparent scoring factor breakdown")

    @field_validator("event_timestamp", mode="before")
    @classmethod
    def validate_utc(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v

    @field_validator("threat_level")
    @classmethod
    def validate_threat_level(cls, v: str) -> str:
        valid_levels = {"Low", "Medium", "High"}
        if v not in valid_levels:
            raise ValueError(f"Threat level must be one of {valid_levels}")
        return v


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    raw_post_ids: Optional[List[str]] = None
    source_ids: Optional[List[str]] = None
    event_type: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    location_name: Optional[str] = None
    location: Optional[GeoJSONPoint] = None
    country_code: Optional[str] = None
    event_timestamp: Optional[datetime] = None
    threat_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    threat_level: Optional[str] = None
    credibility_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    related_event_ids: Optional[List[str]] = None
    corroboration_count: Optional[int] = Field(None, ge=1)
    score_breakdown: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("threat_level")
    @classmethod
    def validate_threat_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_levels = {"Low", "Medium", "High"}
        if v not in valid_levels:
            raise ValueError(f"Threat level must be one of {valid_levels}")
        return v


class EventInDB(EventBase):
    id: Annotated[ObjectId, PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class EventResponse(EventBase):
    id: str = Field(..., description="Database object ID as string")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    total: int = Field(..., description="Total matching events count")
    limit: int = Field(..., description="Page limit")
    skip: int = Field(..., description="Page skip offset")
    items: List[EventResponse] = Field(..., description="List of events")


class EventGlobalMetrics(BaseModel):
    total: int = Field(..., description="Global total events count")
    high: int = Field(..., description="Global High threat events count")
    medium: int = Field(..., description="Global Medium threat events count")
    low: int = Field(..., description="Global Low threat events count")

