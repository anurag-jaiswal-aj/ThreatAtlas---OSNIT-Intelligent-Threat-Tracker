import httpx
from typing import Optional, Tuple
from app.db.session import get_database

USER_AGENT = "ThreatAtlas/1.0 (Student Project)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

async def geocode(location_name: str) -> Optional[Tuple[float, float, Optional[str]]]:
    """
    Geocodes a location name to (lat, lng, country_code).
    Uses a local MongoDB cache to avoid Nominatim rate limits.
    Returns (lat, lng, country_code) or None if not found.
    """
    if not location_name:
        return None

    normalized_name = location_name.strip().lower()

    # 1. Check Cache
    db = get_database()
    cache = db.geocache
    cached = await cache.find_one({"name": normalized_name})
    if cached:
        if cached.get("not_found"):
            return None
        return (cached["lat"], cached["lng"], cached.get("country_code"))

    # 2. Query Nominatim
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                NOMINATIM_URL,
                params={"q": location_name, "format": "json", "limit": 1, "addressdetails": 1},
                headers={"User-Agent": USER_AGENT},
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])

                # Extract country code
                country_code = data[0].get("address", {}).get("country_code")
                if country_code:
                    country_code = country_code.lower()

                # Save to cache
                await cache.insert_one({"name": normalized_name, "lat": lat, "lng": lng, "country_code": country_code})
                return (lat, lng, country_code)
            else:
                # Cache miss
                await cache.insert_one({"name": normalized_name, "not_found": True})
                return None

        except Exception as e:
            # On error, fail gracefully and don't cache
            print(f"Geocoding error for '{location_name}': {e}")
            return None
