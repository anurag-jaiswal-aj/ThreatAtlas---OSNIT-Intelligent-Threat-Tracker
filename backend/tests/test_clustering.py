import pytest
import numpy as np
from datetime import datetime, timedelta
from app.intelligence.clustering import (
    compute_semantic_similarity,
    compute_similarity,
    find_best_matching_event,
)
from app.schemas.event import EventResponse
from app.nlp.schemas import NLPResult, Location
from app.schemas.common import GeoJSONPoint, utc_now

class MockSentenceTransformer:
    def _encode_single(self, text):
        if "bridge" in text or "overpass" in text:
            return np.array([1.0, 1.0, 0.0])
        elif "bank" in text or "interest" in text:
            return np.array([0.0, 0.0, 1.0])
        else:
            return np.array([0.5, 0.5, 0.5])

    def encode(self, text_or_texts):
        if isinstance(text_or_texts, str):
            return self._encode_single(text_or_texts)
        else:
            return [self._encode_single(t) for t in text_or_texts]

@pytest.fixture
def mock_model(mocker):
    return mocker.patch("app.intelligence.clustering.get_semantic_model", return_value=MockSentenceTransformer())

@pytest.fixture
def fallback_model(mocker):
    return mocker.patch("app.intelligence.clustering.get_semantic_model", return_value=None)

def test_semantic_similarity_calculation(mock_model):
    """1. Semantic similarity is calculated correctly using mocked embeddings."""
    mock = MockSentenceTransformer()
    embedding_a = mock.encode("Airstrike destroyed the bridge")

    # 2. Synonymous/semantically similar text
    embedding_b = mock.encode("Aerial bombardment ruined the overpass")
    sim_high = compute_semantic_similarity(embedding_a, embedding_b)
    assert sim_high > 0.99  # Vectors are identical in our mock

    # 3. Clearly unrelated text
    embedding_c = mock.encode("The central bank announced new interest rates")
    sim_low = compute_semantic_similarity(embedding_a, embedding_c)
    assert sim_low == 0.0  # Orthogonal vectors in our mock

def test_post_embedded_only_once(mock_model, mocker):
    """4. The incoming post is embedded only once during candidate matching."""
    encode_spy = mocker.spy(mock_model.return_value, "encode")

    now = utc_now()
    nlp = NLPResult(
        original_text="Airstrike destroyed the bridge",
        cleaned_text="Airstrike destroyed the bridge",
        text="Airstrike destroyed the bridge",
        locations=[],
        organizations=[],
        equipment=[],
        event_types=[],
        confidence_score=0.9
    )

    events = [
        EventResponse(id="1", title="Ev 1", event_timestamp=now, created_at=now, updated_at=now, threat_score=0),
        EventResponse(id="2", title="Ev 2", event_timestamp=now, created_at=now, updated_at=now, threat_score=0),
        EventResponse(id="3", title="Ev 3", event_timestamp=now, created_at=now, updated_at=now, threat_score=0)
    ]

    find_best_matching_event("Airstrike destroyed the bridge", now, nlp, events)

    # Total encode calls: 1 (for post) + 1 (for candidates batch) = 2
    assert encode_spy.call_count == 2
    assert encode_spy.call_args_list[0][0][0] == "Airstrike destroyed the bridge"
    assert isinstance(encode_spy.call_args_list[1][0][0], list)
    assert len(encode_spy.call_args_list[1][0][0]) == 3

def test_geographic_temporal_behavior_intact(fallback_model):
    """5. Existing geographic/temporal matching behavior remains intact (using fallback)."""
    now = utc_now()
    post_loc = (0.0, 0.0)

    event = EventResponse(
        id="1",
        title="Test",
        event_timestamp=now,
        created_at=now,
        updated_at=now,
        threat_score=0,
        location=GeoJSONPoint(coordinates=[0.0, 0.0])
    )

    # Perfect time and space
    score_perfect = compute_similarity(
        post_text="text",
        post_time=now,
        post_location=post_loc,
        post_entities=set(),
        post_embedding=None,
        candidate_embedding=None,
        event=event
    )

    # Temporal rejection (>24h)
    score_bad_time = compute_similarity(
        post_text="text",
        post_time=now + timedelta(hours=25),
        post_location=post_loc,
        post_entities=set(),
        post_embedding=None,
        candidate_embedding=None,
        event=event
    )
    assert score_bad_time == 0.0

    # Spatial rejection (different location)
    event_far = EventResponse(
        id="2",
        title="Test",
        event_timestamp=now,
        created_at=now,
        updated_at=now,
        threat_score=0,
        location=GeoJSONPoint(coordinates=[10.0, 10.0])
    )
    score_bad_space = compute_similarity(
        post_text="text",
        post_time=now,
        post_location=post_loc,
        post_entities=set(),
        post_embedding=None,
        candidate_embedding=None,
        event=event_far
    )
    assert score_bad_space == 0.0

def test_embedding_failure_fallback(mocker):
    """7. Embedding/model failure falls back safely."""
    class FailingModel:
        def encode(self, text):
            raise Exception("Model crashed!")

    mocker.patch("app.intelligence.clustering.get_semantic_model", return_value=FailingModel())

    now = utc_now()
    nlp = NLPResult(
        original_text="Airstrike destroyed the bridge",
        cleaned_text="Airstrike destroyed the bridge",
        text="Airstrike destroyed the bridge",
        locations=[],
        organizations=[],
        equipment=[],
        event_types=[],
        confidence_score=0.9
    )

    event = EventResponse(
        id="1",
        title="Airstrike destroyed the bridge",
        event_timestamp=now,
        created_at=now,
        updated_at=now,
        threat_score=0
    )

    res = find_best_matching_event("Airstrike destroyed the bridge", now, nlp, [event])
    assert res is not None
    assert res[0].id == "1"
