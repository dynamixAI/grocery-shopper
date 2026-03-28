import time
from typing import Optional

import requests


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"


class GeocodingError(Exception):
    """Raised when geocoding fails in a controlled way."""


def geocode_location(query: str) -> Optional[dict]:
    """
    Convert a postcode or area into coordinates using Nominatim.

    Returns:
        dict with:
            - display_name
            - lat
            - lon
        or None if nothing is found.
    """
    cleaned_query = " ".join(query.strip().split())

    if not cleaned_query:
        raise GeocodingError("Location query is empty.")

    headers = {
        "User-Agent": "GroceryShopper/1.0"
    }

    params = {
        "q": cleaned_query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    try:
        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=20
        )
        response.raise_for_status()
        results = response.json()

        # Small pause to stay polite with public API usage
        time.sleep(1)

    except requests.RequestException as exc:
        raise GeocodingError(f"Geocoding request failed: {exc}") from exc

    if not results:
        return None

    top_result = results[0]

    return {
        "display_name": top_result.get("display_name", cleaned_query),
        "lat": float(top_result["lat"]),
        "lon": float(top_result["lon"])
    }
