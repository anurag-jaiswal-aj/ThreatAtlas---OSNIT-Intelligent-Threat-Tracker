from typing import Optional, List, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
from app.schemas.common import PyObjectId
from bson import ObjectId


class WebhookAlertBase(BaseModel):
    url: str = Field(..., description="Webhook URL (must be http or https)")
    provider: Literal["discord", "slack", "generic"] = Field(..., description="Target provider format")
    is_active: bool = Field(default=True)
    min_threat_level: Literal["High", "Critical"] = Field(default="High")
    countries: Optional[List[str]] = Field(default=None, description="List of ISO 3166-1 alpha-2 country codes")
    bbox: Optional[List[List[float]]] = Field(
        default=None,
        description="Geographic bounding box: [[min_lon, min_lat], [max_lon, max_lat]]"
    )

    @validator("url")
    def validate_url_scheme(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("countries", pre=True)
    def normalize_countries(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("countries must be a list")
        # Normalize to lowercase and reject empty
        normalized = []
        for c in v:
            if not isinstance(c, str):
                raise ValueError("Country code must be a string")
            c = c.strip().lower()
            if not c or len(c) != 2:
                raise ValueError("Country code must be 2 characters")
            normalized.append(c)
        return normalized if normalized else None

    @validator("bbox")
    def validate_bbox(cls, v):
        if v is None:
            return v
        if len(v) != 2 or len(v[0]) != 2 or len(v[1]) != 2:
            raise ValueError("bbox must be in format [[min_lon, min_lat], [max_lon, max_lat]]")
        min_lon, min_lat = v[0]
        max_lon, max_lat = v[1]
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if min_lon > max_lon or min_lat > max_lat:
            raise ValueError("Invalid bounding box min/max ordering")
        return v


class WebhookAlertCreate(WebhookAlertBase):
    pass


class WebhookAlertUpdate(BaseModel):
    url: Optional[str] = None
    provider: Optional[Literal["discord", "slack", "generic"]] = None
    is_active: Optional[bool] = None
    min_threat_level: Optional[Literal["High", "Critical"]] = None
    countries: Optional[List[str]] = None
    bbox: Optional[List[List[float]]] = None

    @validator("url")
    def validate_url_scheme(cls, v):
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("countries", pre=True)
    def normalize_countries(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("countries must be a list")
        normalized = [c.strip().lower() for c in v if isinstance(c, str) and c.strip()]
        return normalized if normalized else None

    @validator("bbox")
    def validate_bbox(cls, v):
        if v is None:
            return v
        if len(v) != 2 or len(v[0]) != 2 or len(v[1]) != 2:
            raise ValueError("bbox must be in format [[min_lon, min_lat], [max_lon, max_lat]]")
        min_lon, min_lat = v[0]
        max_lon, max_lat = v[1]
        if min_lon > max_lon or min_lat > max_lat:
            raise ValueError("Invalid bounding box min/max ordering")
        return v


class WebhookAlertResponse(WebhookAlertBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}
