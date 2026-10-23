"""Submit-time place lookup and coarse reverse geocoding via Nominatim."""
import os
import threading
import time

import requests

from .cache import TTLCache

NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
USER_AGENT = "SafeRouteAI/1.0 (https://github.com/harishgit0/AI-Tourist-Safety-Predictor)"
LOOKUP_CACHE = TTLCache(ttl=86400, maxsize=1000, namespace="nominatim")
_request_lock = threading.Lock()
_last_request_at = 0.0


class GeocodingError(Exception):
    """The place lookup provider could not resolve a location."""


def _request(path, params):
    global _last_request_at
    # Public Nominatim policy requires no more than one request per second per app.
    with _request_lock:
        delay = 1.05 - (time.monotonic() - _last_request_at)
        if delay > 0:
            time.sleep(delay)
        _last_request_at = time.monotonic()
        try:
            response = requests.get(
                f"{NOMINATIM_URL.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=8,
            )
            if response.status_code == 429:
                raise GeocodingError("Place search is busy. Wait a moment and try again.")
            response.raise_for_status()
            return response.json()
        except GeocodingError:
            raise
        except (requests.RequestException, ValueError) as exc:
            raise GeocodingError("Place lookup is temporarily unavailable. Please retry.") from exc


def _display_name(item):
    address = item.get("address") or {}
    parts = []
    for key in ("neighbourhood", "suburb", "city", "town", "village", "state", "country"):
        value = address.get(key)
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts) or str(item.get("display_name") or item.get("name") or "Selected location")


def search_place(query):
    query = " ".join(str(query or "").split())
    if len(query) < 2 or len(query) > 160:
        raise ValueError("Enter a place name between 2 and 160 characters.")
    key = ("search", query.casefold())
    cached = LOOKUP_CACHE.get(key)
    if cached:
        return cached

    results = _request("search", {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "en",
    })
    if not isinstance(results, list) or not results:
        raise LookupError(f'No place found for "{query}". Try adding its city or country.')
    result = results[0]
    place = {
        "lat": float(result["lat"]),
        "lng": float(result["lon"]),
        "name": str(result.get("name") or query)[:120],
        "label": _display_name(result)[:220],
    }
    LOOKUP_CACHE.set(key, place)
    return place


def reverse_place(lat, lng):
    # Round to roughly a neighbourhood-sized area before requesting a label,
    # so the geocoder does not receive the browser's exact GPS coordinates.
    lat = round(float(lat), 2)
    lng = round(float(lng), 2)
    key = ("reverse", lat, lng)
    cached = LOOKUP_CACHE.get(key)
    if cached:
        return cached

    result = _request("reverse", {
        "lat": lat,
        "lon": lng,
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 14,
        "accept-language": "en",
    })
    if not isinstance(result, dict) or result.get("error"):
        raise LookupError("Could not find a nearby place name for your current location.")
    place = {"label": _display_name(result)[:220], "lat": lat, "lng": lng}
    LOOKUP_CACHE.set(key, place)
    return place
