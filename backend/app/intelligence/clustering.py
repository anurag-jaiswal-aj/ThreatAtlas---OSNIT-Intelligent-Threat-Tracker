import math
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from app.nlp.schemas import NLPResult, Location
from app.schemas.event import EventResponse
from app.intelligence.config import (
    MAX_SPATIAL_DISTANCE_KM,
    MAX_TEMPORAL_WINDOW_SECONDS,
    MIN_CLUSTER_MATCH_SCORE,
)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great-Circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two sets."""
    if not set_a and not set_b:
        return 0.0
    union = set_a.union(set_b)
    if not union:
        return 0.0
    intersection = set_a.intersection(set_b)
    return len(intersection) / len(union)

def extract_text_tokens(text: str) -> Set[str]:
    """Tokenize clean text into lowercased words for lightweight similarity comparison."""
    if not text:
        return set()
    words = text.lower().split()
    stop_words = {"the", "a", "an", "in", "on", "at", "and", "or", "to", "of", "for", "with", "by", "is", "are", "was", "were"}
    return {w.strip(".,!?:;\"'()") for w in words if len(w) > 2 and w not in stop_words}

def compute_similarity(
    post_text: str,
    post_time: datetime,
    post_location: Optional[Tuple[float, float]],
    post_entities: Set[str],
    event: EventResponse,
) -> float:
    """
    Compute a deterministic composite similarity match score between a post and an existing Event.
    Returns 0.0 if hard constraints fail (e.g. >50km distance or >24h time difference).
    """
    # 1. Temporal Check
    event_time = event.event_timestamp
    time_diff_seconds = abs((post_time - event_time).total_seconds())
    if time_diff_seconds > MAX_TEMPORAL_WINDOW_SECONDS:
        return 0.0
    time_score = 1.0 - (time_diff_seconds / MAX_TEMPORAL_WINDOW_SECONDS)

    # 2. Spatial / Geographic Check
    event_coords = None
    if event.location and event.location.coordinates and len(event.location.coordinates) == 2:
        # GeoJSON is [lng, lat]
        event_coords = (event.location.coordinates[1], event.location.coordinates[0])

    spatial_match = None
    if post_location and event_coords:
        dist_km = haversine_distance_km(post_location[0], post_location[1], event_coords[0], event_coords[1])
        if dist_km > MAX_SPATIAL_DISTANCE_KM:
            # Case 5 & Case 3 Hard rejection: Different locations / >50km apart MUST NOT merge
            return 0.0
        spatial_match = 1.0 - (dist_km / MAX_SPATIAL_DISTANCE_KM)

    # 3. Entity Similarity
    event_entities: Set[str] = set()
    if event.entities:
        for cat_list in event.entities.values():
            event_entities.update(item.lower() for item in cat_list)
    entity_sim = jaccard_similarity(post_entities, event_entities)

    # 4. Lightweight Text Similarity
    event_text = f"{event.title} {event.summary or ''}"
    text_tokens_post = extract_text_tokens(post_text)
    text_tokens_event = extract_text_tokens(event_text)
    text_sim = jaccard_similarity(text_tokens_post, text_tokens_event)

    # Composite Weighted Scoring
    if spatial_match is not None:
        score = 0.35 * spatial_match + 0.25 * time_score + 0.20 * entity_sim + 0.20 * text_sim
    else:
        score = 0.40 * time_score + 0.30 * entity_sim + 0.30 * text_sim

    return round(score, 4)

def find_best_matching_event(
    post_text: str,
    post_time: datetime,
    nlp_result: NLPResult,
    candidate_events: List[EventResponse],
) -> Optional[Tuple[EventResponse, float]]:
    """
    Find the best matching candidate event for a given post and NLP result.
    Returns (best_event, score) if score >= MIN_CLUSTER_MATCH_SCORE, else None.
    """
    if not candidate_events:
        return None

    # Determine post primary location coords
    post_location: Optional[Tuple[float, float]] = None
    if nlp_result.locations:
        for loc in nlp_result.locations:
            if loc.confidence != "unknown" and (loc.lat != 0.0 or loc.lng != 0.0):
                post_location = (loc.lat, loc.lng)
                break

    # Gather all post extracted entity strings
    post_entities: Set[str] = set()
    post_entities.update(eq.lower() for eq in nlp_result.equipment)
    post_entities.update(ev.lower() for ev in nlp_result.event_types)
    post_entities.update(org.lower() for org in nlp_result.organizations)
    post_entities.update(loc.name.lower() for loc in nlp_result.locations)

    best_match: Optional[EventResponse] = None
    highest_score: float = 0.0

    for event in candidate_events:
        score = compute_similarity(post_text, post_time, post_location, post_entities, event)
        if score > highest_score:
            highest_score = score
            best_match = event

    if best_match and highest_score >= MIN_CLUSTER_MATCH_SCORE:
        return (best_match, highest_score)
    return None
