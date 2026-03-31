import math
from typing import List

import requests

from services.geocoding import GeocodingError, geocode_location


OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


class StoreLookupError(Exception):
    """Raised when store lookup fails in a controlled way."""


def miles_to_metres(miles: float) -> float:
    return miles * 1609.344


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_miles = 3958.8

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return earth_radius_miles * c


def normalise_brand_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())

    mapping = {
        "Sainsburys": "Sainsbury's",
        "Sainsbury’s": "Sainsbury's",
        "ASDA": "Asda",
        "ALDI": "Aldi",
        "LIDL": "Lidl",
        "FARMFOODS": "Farmfoods",
    }

    return mapping.get(cleaned, cleaned)


def is_brand_match(place_name: str, selected_brands: List[str]) -> bool:
    lower_name = place_name.lower().replace("'", "")

    for brand in selected_brands:
        brand_lower = brand.lower().replace("'", "")
        if brand_lower in lower_name:
            return True

    return False


def build_overpass_query(lat: float, lon: float, radius_metres: float) -> str:
    """
    Keep the query as small as possible to reduce timeouts.
    """
    radius_int = int(radius_metres)

    return f"""
    [out:json][timeout:25];
    (
      node(around:{radius_int},{lat},{lon})["shop"="supermarket"];
      node(around:{radius_int},{lat},{lon})["shop"="convenience"];
      node(around:{radius_int},{lat},{lon})["shop"="grocery"];
      way(around:{radius_int},{lat},{lon})["shop"="supermarket"];
      way(around:{radius_int},{lat},{lon})["shop"="convenience"];
      way(around:{radius_int},{lat},{lon})["shop"="grocery"];
    );
    out center tags;
    """


def fetch_overpass_payload(query: str) -> dict:
    headers = {
        "User-Agent": "GroceryShopper/1.0"
    }

    last_error = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers=headers,
                timeout=40
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            last_error = exc
            continue
        except ValueError as exc:
            last_error = exc
            continue

    raise StoreLookupError(f"Store lookup request failed: {last_error}")


def lookup_nearby_stores(
    location_query: str,
    radius_miles: float,
    selected_brands: List[str]
) -> List[dict]:
    if not selected_brands:
        return []

    try:
        location_result = geocode_location(location_query)
    except GeocodingError as exc:
        raise StoreLookupError(str(exc)) from exc

    if location_result is None:
        return []

    user_lat = location_result["lat"]
    user_lon = location_result["lon"]
    radius_metres = miles_to_metres(radius_miles)

    query = build_overpass_query(user_lat, user_lon, radius_metres)
    payload = fetch_overpass_payload(query)

    elements = payload.get("elements", [])
    store_results = []

    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name", "").strip()

        if not name:
            continue

        if not is_brand_match(name, selected_brands):
            continue

        if "lat" in element and "lon" in element:
            store_lat = element["lat"]
            store_lon = element["lon"]
        else:
            center = element.get("center")
            if not center:
                continue
            store_lat = center["lat"]
            store_lon = center["lon"]

        distance_miles = haversine_distance_miles(user_lat, user_lon, store_lat, store_lon)

        if distance_miles > radius_miles:
            continue

        matched_brand = None
        for selected_brand in selected_brands:
            if selected_brand.lower().replace("'", "") in name.lower().replace("'", ""):
                matched_brand = selected_brand
                break

        address_parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
            tags.get("addr:city", ""),
            tags.get("addr:postcode", "")
        ]
        address = ", ".join(part for part in address_parts if part).strip()

        if not address:
            address = "Address not available"

        store_results.append({
            "store_brand": normalise_brand_name(matched_brand or name),
            "branch": name,
            "address": address,
            "distance_miles": round(distance_miles, 2),
            "lat": store_lat,
            "lon": store_lon
        })

    unique_results = []
    seen = set()

    for store in sorted(store_results, key=lambda x: x["distance_miles"]):
        key = (
            store["store_brand"].lower(),
            store["branch"].lower(),
            store["address"].lower()
        )
        if key not in seen:
            seen.add(key)
            unique_results.append(store)

    return unique_results
