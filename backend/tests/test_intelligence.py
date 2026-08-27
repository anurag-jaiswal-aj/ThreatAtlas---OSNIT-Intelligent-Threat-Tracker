from datetime import datetime, timezone, timedelta
import pytest
from app.nlp.schemas import NLPResult, Entity, Location
from app.schemas.common import GeoJSONPoint
from app.schemas.event import EventResponse
from app.intelligence.threat_scorer import calculate_threat_score
from app.intelligence.credibility_scorer import calculate_credibility_score
from app.intelligence.clustering import (
    compute_similarity,
    find_best_matching_event,
    haversine_distance_km,
)
from app.ingestion.config import DEFAULT_RSS_FEEDS
from app.intelligence.config import SOURCE_RELIABILITY_MAP, DEFAULT_SOURCE_RELIABILITY

# ==========================================
# 1. THREAT SCORING TESTS
# ==========================================

def test_threat_scoring_low_severity():
    nlp_res = NLPResult(
        original_text="Routine peaceful weather announcement.",
        cleaned_text="Routine peaceful weather announcement.",
        entities=[],
        locations=[],
        organizations=[],
        equipment=[],
        event_types=[],
    )
    score, level, breakdown = calculate_threat_score(nlp_res, corroboration_count=1)
    assert score <= 39.0
    assert level == "Low"
    assert breakdown["total"] == score
    assert 0.0 <= score <= 100.0

def test_threat_scoring_medium_severity():
    nlp_res = NLPResult(
        original_text="Attack reported in the city center. Drone spotted.",
        cleaned_text="Attack reported in the city center. Drone spotted.",
        entities=[],
        locations=[Location(name="City Center", lat=48.85, lng=2.35, confidence="high")],
        organizations=[],
        equipment=["drone"],
        event_types=["attack"],
    )
    score, level, breakdown = calculate_threat_score(nlp_res, corroboration_count=1)
    assert 40.0 <= score <= 69.0
    assert level == "Medium"
    assert breakdown["action_score"] > 0
    assert breakdown["equipment_score"] > 0
    assert 0.0 <= score <= 100.0

def test_threat_scoring_high_severity():
    nlp_res = NLPResult(
        original_text="Heavy airstrike and explosion reported in Kyiv. F-16 and T-72 deployment confirmed.",
        cleaned_text="Heavy airstrike and explosion reported in Kyiv. F-16 and T-72 deployment confirmed.",
        entities=[],
        locations=[Location(name="Kyiv", lat=50.45, lng=30.52, confidence="high")],
        organizations=[],
        equipment=["F-16", "T-72"],
        event_types=["airstrike", "explosion"],
    )
    score, level, breakdown = calculate_threat_score(nlp_res, corroboration_count=3)
    assert score >= 70.0
    assert level == "High"
    assert breakdown["location_score"] == 20.0  # Sensitive location Kyiv
    assert 0.0 <= score <= 100.0

def test_threat_scoring_unknown_location_neutral():
    nlp_res_unknown = NLPResult(
        original_text="Unspecified report in unknown location.",
        cleaned_text="Unspecified report in unknown location.",
        entities=[],
        locations=[Location(name="Unknown Spot XYZ", lat=0.0, lng=0.0, confidence="unknown")],
        organizations=[],
        equipment=[],
        event_types=[],
    )
    score, level, breakdown = calculate_threat_score(nlp_res_unknown, corroboration_count=1)
    assert breakdown["location_score"] == 5.0  # Default neutral score

def test_threat_scoring_clamping():
    # Force extreme high values
    nlp_res = NLPResult(
        original_text="Airstrike explosion bombing shelling with F-16 T-72 missile artillery in Kyiv Taipei.",
        cleaned_text="Airstrike explosion bombing shelling with F-16 T-72 missile artillery in Kyiv Taipei.",
        entities=[],
        locations=[
            Location(name="Kyiv", lat=50.45, lng=30.52, confidence="high"),
            Location(name="Taipei", lat=25.03, lng=121.56, confidence="high"),
        ],
        organizations=[],
        equipment=["F-16", "T-72", "missile", "artillery"],
        event_types=["airstrike", "explosion", "bombing", "shelling"],
    )
    score, level, breakdown = calculate_threat_score(nlp_res, corroboration_count=10)
    assert score == 100.0
    assert level == "High"


# ==========================================
# 2. CREDIBILITY SCORING TESTS
# ==========================================

def test_credibility_single_source():
    score, breakdown = calculate_credibility_score(["reuters"])
    assert score == 90.0
    assert breakdown["independent_source_count"] == 1
    assert breakdown["corroboration_bonus"] == 0.0

def test_credibility_multiple_independent_sources():
    score, breakdown = calculate_credibility_score(["reuters", "bbc", "al jazeera"])
    assert score == 100.0  # 90 base + 15 bonus clamped to 100
    assert breakdown["independent_source_count"] == 3
    assert breakdown["corroboration_bonus"] == 15.0

def test_credibility_duplicate_same_source_reports():
    # Multiple copies of the SAME article from the same source count as 1 independent source
    score, breakdown = calculate_credibility_score(["bbc", "bbc", "bbc"])
    assert score == 90.0
    assert breakdown["independent_source_count"] == 1
    assert breakdown["corroboration_bonus"] == 0.0

def test_credibility_reliable_vs_low_reliability():
    score_rel, _ = calculate_credibility_score(["reuters"])
    score_low, _ = calculate_credibility_score(["telegram"])
    assert score_rel > score_low
    assert score_low == 50.0  # Base for telegram

def test_credibility_new_defense_sources():
    sources = [
        "defense news",
        "reuters world",
        "reliefweb crisis reports",
        "us naval institute news",
        "uk mod / security announcements"
    ]
    for source in sources:
        score, _ = calculate_credibility_score([source])
        assert score == SOURCE_RELIABILITY_MAP[source]
        assert score != DEFAULT_SOURCE_RELIABILITY

def test_feed_registry_sources_exist():
    expected_feeds = [
        "Defense News",
        "Reuters World",
        "ReliefWeb Crisis Reports",
        "US Naval Institute News",
        "UK MOD / Security Announcements"
    ]
    feed_names = [feed.name for feed in DEFAULT_RSS_FEEDS]
    
    for expected in expected_feeds:
        assert expected in feed_names
        
        feed_config = next(f for f in DEFAULT_RSS_FEEDS if f.name == expected)
        assert feed_config.url.strip() != ""
        
        mapped_key = expected.lower()
        assert mapped_key in SOURCE_RELIABILITY_MAP
        assert SOURCE_RELIABILITY_MAP[mapped_key] != DEFAULT_SOURCE_RELIABILITY


# ==========================================
# 3. EVENT CLUSTERING TESTS
# ==========================================

@pytest.fixture
def base_time():
    return datetime(2026, 8, 12, 12, 0, 0, tzinfo=timezone.utc)

def create_mock_event(
    event_id: str,
    title: str,
    summary: str,
    event_time: datetime,
    lat: float,
    lng: float,
    event_type: str = "explosion",
    equipment: list = None,
) -> EventResponse:
    return EventResponse(
        id=event_id,
        title=title,
        summary=summary,
        raw_post_ids=["p1"],
        source_ids=["reuters"],
        event_type=event_type,
        entities={"locations": ["Paris"], "organizations": [], "equipment": equipment or []},
        location_name="Paris",
        location=GeoJSONPoint(coordinates=[lng, lat]),
        event_timestamp=event_time,
        threat_score=50.0,
        threat_level="Medium",
        credibility_score=90.0,
        corroboration_count=1,
        created_at=event_time,
        updated_at=event_time,
    )

def test_clustering_case_2_different_sources_same_location_time_event(base_time):
    """Case 2: Different sources, same location/time/event -> same cluster/event"""
    event = create_mock_event(
        event_id="65d000000000000000000001",
        title="Explosion in Paris",
        summary="A major explosion was reported in central Paris near Eiffel Tower.",
        event_time=base_time,
        lat=48.8566,
        lng=2.3522,
    )
    
    nlp_res = NLPResult(
        original_text="Al Jazeera: Blast hits Paris near Eiffel Tower.",
        cleaned_text="Al Jazeera: Blast hits Paris near Eiffel Tower.",
        entities=[],
        locations=[Location(name="Paris", lat=48.8566, lng=2.3522, confidence="high")],
        organizations=[],
        equipment=[],
        event_types=["explosion"],
    )
    
    match = find_best_matching_event(
        post_text="Al Jazeera: Blast hits Paris near Eiffel Tower.",
        post_time=base_time + timedelta(minutes=30),
        nlp_result=nlp_res,
        candidate_events=[event],
    )
    
    assert match is not None
    matched_evt, match_score = match
    assert matched_evt.id == event.id
    assert match_score >= 0.55

def test_clustering_case_3_different_locations(base_time):
    """Case 3: Different locations -> different events"""
    event_paris = create_mock_event(
        event_id="65d000000000000000000001",
        title="Explosion in Paris",
        summary="Explosion in Paris.",
        event_time=base_time,
        lat=48.8566,
        lng=2.3522,
    )
    
    # Location is Berlin (~878 km away from Paris)
    nlp_res_berlin = NLPResult(
        original_text="Explosion in Berlin.",
        cleaned_text="Explosion in Berlin.",
        entities=[],
        locations=[Location(name="Berlin", lat=52.5200, lng=13.4050, confidence="high")],
        organizations=[],
        equipment=[],
        event_types=["explosion"],
    )
    
    match = find_best_matching_event(
        post_text="Explosion in Berlin.",
        post_time=base_time,
        nlp_result=nlp_res_berlin,
        candidate_events=[event_paris],
    )
    
    assert match is None

def test_clustering_case_4_far_apart_in_time(base_time):
    """Case 4: Same location but far apart in time (>24h) -> different events"""
    event = create_mock_event(
        event_id="65d000000000000000000001",
        title="Explosion in Paris",
        summary="Explosion in Paris.",
        event_time=base_time,
        lat=48.8566,
        lng=2.3522,
    )
    
    nlp_res = NLPResult(
        original_text="Explosion in Paris.",
        cleaned_text="Explosion in Paris.",
        entities=[],
        locations=[Location(name="Paris", lat=48.8566, lng=2.3522, confidence="high")],
        organizations=[],
        equipment=[],
        event_types=["explosion"],
    )
    
    match = find_best_matching_event(
        post_text="Explosion in Paris.",
        post_time=base_time + timedelta(hours=48),  # 48 hours later
        nlp_result=nlp_res,
        candidate_events=[event],
    )
    
    assert match is None

def test_clustering_case_5_similar_text_unrelated_locations(base_time):
    """Case 5: Similar text but unrelated locations (>50km apart) -> do not merge"""
    event = create_mock_event(
        event_id="65d000000000000000000001",
        title="Protest erupts in Paris center with drone surveillance",
        summary="Protest erupts in Paris center with drone surveillance",
        event_time=base_time,
        lat=48.8566,
        lng=2.3522,
        equipment=["drone"],
    )
    
    nlp_res_lyon = NLPResult(
        original_text="Protest erupts in Lyon center with drone surveillance",
        cleaned_text="Protest erupts in Lyon center with drone surveillance",
        entities=[],
        locations=[Location(name="Lyon", lat=45.7640, lng=4.8357, confidence="high")], # Lyon is ~390km from Paris
        organizations=[],
        equipment=["drone"],
        event_types=["protest"],
    )
    
    match = find_best_matching_event(
        post_text="Protest erupts in Lyon center with drone surveillance",
        post_time=base_time,
        nlp_result=nlp_res_lyon,
        candidate_events=[event],
    )
    
    assert match is None  # Must not merge due to >50km distance constraint

def test_clustering_determinism(base_time):
    """Verify that clustering results are 100% deterministic given identical inputs"""
    event = create_mock_event(
        event_id="65d000000000000000000001",
        title="Explosion in Paris",
        summary="Explosion in Paris.",
        event_time=base_time,
        lat=48.8566,
        lng=2.3522,
    )
    nlp_res = NLPResult(
        original_text="Explosion reported near Eiffel Tower in Paris.",
        cleaned_text="Explosion reported near Eiffel Tower in Paris.",
        entities=[],
        locations=[Location(name="Paris", lat=48.8566, lng=2.3522, confidence="high")],
        organizations=[],
        equipment=[],
        event_types=["explosion"],
    )
    
    res1 = find_best_matching_event("Explosion reported near Eiffel Tower in Paris.", base_time, nlp_res, [event])
    res2 = find_best_matching_event("Explosion reported near Eiffel Tower in Paris.", base_time, nlp_res, [event])
    
    assert res1 is not None and res2 is not None
    assert res1[0].id == res2[0].id
    assert res1[1] == res2[1]
