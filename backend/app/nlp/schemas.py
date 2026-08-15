from typing import List, Optional
from pydantic import BaseModel, Field

class Entity(BaseModel):
    text: str
    label: str
    start_char: int
    end_char: int

class Location(BaseModel):
    name: str
    lat: float
    lng: float
    confidence: str = Field(default="unknown", description="e.g., high, medium, low, unknown")

class NLPResult(BaseModel):
    original_text: str
    cleaned_text: str
    entities: List[Entity] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    event_types: List[str] = Field(default_factory=list)
