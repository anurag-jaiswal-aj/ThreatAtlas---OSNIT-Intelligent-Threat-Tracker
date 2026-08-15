from typing import Any, Dict, List, Tuple
from app.intelligence.config import (
    SOURCE_RELIABILITY_MAP,
    DEFAULT_SOURCE_RELIABILITY,
)

def calculate_credibility_score(
    source_ids: List[str],
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates a 0-100 credibility score based on source reliability and independent corroboration.
    
    IMPORTANT:
    Multiple posts from the same source count as 1 independent source.
    """
    if not source_ids:
        return 50.0, {
            "base_source_reliability": 50.0,
            "independent_source_count": 0,
            "corroboration_bonus": 0.0,
            "total": 50.0,
        }

    # Normalize and deduplicate source identifiers
    normalized_sources = set(src.strip().lower() for src in source_ids if src)
    independent_count = len(normalized_sources)

    # 1. Base Source Reliability: Max reliability among unique sources
    source_reliabilities = [
        SOURCE_RELIABILITY_MAP.get(src, DEFAULT_SOURCE_RELIABILITY)
        for src in normalized_sources
    ]
    max_base_reliability = max(source_reliabilities) if source_reliabilities else DEFAULT_SOURCE_RELIABILITY

    # 2. Independent Corroboration Bonus:
    # 1 independent source = 0 bonus
    # 2 independent sources = +10 bonus
    # 3 independent sources = +15 bonus
    # 4+ independent sources = +20 bonus
    if independent_count <= 1:
        corroboration_bonus = 0.0
    elif independent_count == 2:
        corroboration_bonus = 10.0
    elif independent_count == 3:
        corroboration_bonus = 15.0
    else:
        corroboration_bonus = 20.0

    raw_total = max_base_reliability + corroboration_bonus
    total_score = round(min(100.0, max(0.0, raw_total)), 1)

    breakdown = {
        "max_base_source_reliability": round(max_base_reliability, 1),
        "independent_source_count": independent_count,
        "corroboration_bonus": round(corroboration_bonus, 1),
        "total": total_score,
    }

    return total_score, breakdown
