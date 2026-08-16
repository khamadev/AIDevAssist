"""Fetches real points of interest for a destination.

Uses OpenStreetMap's Nominatim (geocoding) and Overpass (POI query) APIs —
the same free, open-license (ODbL) data source already used for the map on
the trip page. Deliberately not scraping any commercial travel site's HTML:
that would risk violating their Terms of Service and is fragile (breaks the
moment their markup changes). Both functions never raise — a network
failure or empty result just means the caller falls back to generic
content, not a broken endpoint.
"""

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# overpass-api.de (the "default" public instance) is frequently overloaded
# and returns 504s under normal load — confirmed happening for real
# destinations during testing, not a rare edge case. Try multiple public
# mirrors in order rather than depending on a single, often-overloaded
# server; only fall back to generic itinerary content if all of them fail.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
# Both Nominatim and Overpass reject requests with a missing/generic
# User-Agent (returns 406) as part of their usage policy — this is not
# optional.
USER_AGENT = "travel-planner-app"
REQUEST_TIMEOUT = 6.0
# Overpass's public instance can be slow under load; give it more room
# than Nominatim's simple lookup, matching the query's own internal
# [timeout:10].
OVERPASS_TIMEOUT = 11.0
DEFAULT_RADIUS_M = 2000
DEFAULT_LIMIT = 30

# OSM tags that map to each category we plan itinerary slots around.
_CATEGORY_TAG_FILTERS = [
    ('"tourism"="attraction"', "sight"),
    ('"tourism"="museum"', "sight"),
    ('"historic"', "sight"),
    ('"amenity"="restaurant"', "food"),
    ('"amenity"="cafe"', "food"),
    ('"leisure"="park"', "nature"),
    ('"natural"="beach"', "nature"),
]


def geocode(destination: str) -> tuple[float, float] | None:
    """Returns (lat, lon) for a destination, or None if it can't be found."""
    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={"q": destination, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None


def fetch_points_of_interest(
    lat: float,
    lon: float,
    radius_m: int = DEFAULT_RADIUS_M,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """Query Overpass for named POIs near (lat, lon).

    Returns a list of {"name": str, "category": "sight"|"food"|"nature"}
    dicts, deduplicated by name. Returns [] on any failure.
    """
    filters = "".join(
        f"node[{tag}](around:{radius_m},{lat},{lon});" for tag, _category in _CATEGORY_TAG_FILTERS
    )
    query = f"[out:json][timeout:10];({filters});out center {limit};"

    elements = _query_overpass_mirrors(query)
    if elements is None:
        return []

    pois: list[dict] = []
    seen_names: set[str] = set()
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        pois.append({"name": name, "category": _categorize(tags)})
    return pois


def _query_overpass_mirrors(query: str) -> list[dict] | None:
    """Try each Overpass mirror in order, returning the first successful
    response's elements. Returns None only if every mirror fails.
    """
    for url in OVERPASS_URLS:
        try:
            response = httpx.post(
                url,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=OVERPASS_TIMEOUT,
            )
            response.raise_for_status()
            return response.json().get("elements", [])
        except (httpx.HTTPError, ValueError):
            continue
    return None


def _categorize(tags: dict) -> str:
    if tags.get("amenity") in ("restaurant", "cafe"):
        return "food"
    if tags.get("leisure") == "park" or tags.get("natural") == "beach":
        return "nature"
    return "sight"
