"""Google Routes API integration and sampled risk comparison for walking routes."""
import os
from datetime import datetime

import requests

from .scoring import UpstreamError, analyze, load_models, nearest_record
from .cache import TTLCache

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTE_CACHE = TTLCache(ttl=300, maxsize=100)
MAX_ROUTES = 3
SAMPLES_PER_ROUTE = 1


class RoutesProviderError(Exception):
    """The Google Routes API could not provide a route."""


def _valid_point(point, label):
    if not isinstance(point, dict):
        raise ValueError(f"{label} must contain lat and lng.")
    try:
        lat, lng = float(point["lat"]), float(point["lng"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{label}.lat and {label}.lng are required numbers.")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError(f"{label} coordinates are out of range.")
    return {
        "lat": lat,
        "lng": lng,
        "name": str(point.get("name") or f"{lat:.4f}, {lng:.4f}")[:120],
    }


def decode_polyline(encoded):
    """Decode Google's encoded polyline into [{lat, lng}, ...]."""
    points, index, lat, lng = [], 0, 0, 0
    while index < len(encoded):
        values = []
        for _ in range(2):
            result, shift = 0, 0
            while True:
                if index >= len(encoded):
                    raise ValueError("Malformed encoded polyline.")
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            values.append(~(result >> 1) if result & 1 else (result >> 1))
        lat += values[0]
        lng += values[1]
        points.append({"lat": lat / 1e5, "lng": lng / 1e5})
    return points


def _route_samples(path):
    """Choose one midpoint sample along the route."""
    if not path:
        return []
    return [path[len(path) // 2]]


def _duration_seconds(value):
    """Convert a Routes API duration string such as '123s' to seconds."""
    try:
        return int(float(str(value).removesuffix("s")))
    except (TypeError, ValueError):
        return None


def _historical_sample(point):
    """Score a point using a nearby historical grid cell."""
    _, spatial = load_models()
    hist = nearest_record(spatial["cells"], point["lat"], point["lng"])

    if hist is None:
        # No historical cell within the existing 450 m matching radius.
        raise UpstreamError("No historical grid cell was found within 450 metres.")

    score = max(0, min(100, int(round(float(hist["label"])))))
    level = "Safe" if score < 40 else "Moderate" if score < 70 else "Risky"

    return {
        "lat": point["lat"],
        "lng": point["lng"],
        "score": score,
        "level": level,
        "confidence": "Low",
        "factors_used": 1,
        "factors_total": 1,
        "missing_factors": [
            "live_poi_features",
            "current_time_weather_adjustment",
        ],
        "source": "historical_grid",
        "historical_total_crimes": int(hist["total_crimes"]),
        "note": (
            "Historical grid average only; live POI scoring and "
            "current time/weather adjustments were unavailable."
        ),
    }


def _score_sample(point, visit_dt, live_scoring_failed=None):
    """Try live scoring unless it already failed for this request; then use history."""
    print(f"[ROUTES DEBUG] Scoring sample: {point}", flush=True)

    key = (
        round(point["lat"], 4),
        round(point["lng"], 4),
        visit_dt.isoformat(timespec="minutes") if visit_dt else "now",
    )

    cached = ROUTE_CACHE.get(key)
    if cached is not None:
        return cached

    # Once live scoring fails for this comparison request, skip repeat network
    # attempts but still score each route independently from the historical grid.
    skip_live = live_scoring_failed is not None and live_scoring_failed[0]

    if not skip_live:
        try:
            print("[ROUTES DEBUG] Calling analyze()", flush=True)
            result = analyze(
                point["lat"],
                point["lng"],
                "Route sample",
                visit_dt,
                fast=True,
            )

            sample = {
                "lat": point["lat"],
                "lng": point["lng"],
                "score": result["score"],
                "level": result["level"],
                "confidence": result["confidence"]["label"],
                "factors_used": result["factors_used"],
                "factors_total": result["factors_total"],
                "missing_factors": result["missing_factors"],
                "source": "live_model",
            }
            print("[ROUTES DEBUG] analyze() completed", flush=True)

        except UpstreamError as exc:
            if live_scoring_failed is not None:
                live_scoring_failed[0] = True
            print(
                f"[ROUTES DEBUG] Live scoring unavailable: {exc}. "
                "Trying historical grid.",
                flush=True,
            )
            sample = _historical_sample(point)
    else:
        print(
            "[ROUTES DEBUG] Skipping live scoring after earlier "
            "OpenStreetMap failure; using historical grid.",
            flush=True,
        )
        sample = _historical_sample(point)

    if sample["source"] == "historical_grid":
        print(
            f"[ROUTES DEBUG] Historical fallback: score={sample['score']}, "
            f"level={sample['level']}",
            flush=True,
        )

    ROUTE_CACHE.set(key, sample)
    return sample


def _compare_route(route, index, visit_dt, live_scoring_failed=None):
    encoded = route.get("polyline", {}).get("encodedPolyline")
    if not encoded:
        raise RoutesProviderError("Google returned a route without a polyline.")

    path = decode_polyline(encoded)
    samples = _route_samples(path)
    scored, failures = [], 0

    for point in samples:
        try:
            scored.append(_score_sample(point, visit_dt, live_scoring_failed))
        except (UpstreamError, RuntimeError, requests.RequestException) as exc:
            print(
                f"[ROUTES DEBUG] Sample scoring failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            failures += 1

    if not scored:
        risk = None
        level = "Unavailable"
        confidence = "Low"
    else:
        risk = round(sum(item["score"] for item in scored) / len(scored))
        level = "Safe" if risk < 40 else "Moderate" if risk < 70 else "Risky"
        confidence_rank = {"Low": 0, "Medium": 1, "High": 2}
        confidence = min(
            (item["confidence"] for item in scored),
            key=lambda value: confidence_rank.get(value, 0),
        )

    return {
        "id": f"route-{index + 1}",
        "label": "Recommended by Google" if index == 0 else f"Alternative {index}",
        "distance_meters": route.get("distanceMeters"),
        "duration_seconds": _duration_seconds(route.get("duration")),
        "polyline": encoded,
        "path": path,
        "estimated_risk_score": risk,
        "estimated_risk_level": level,
        "confidence": confidence,
        "sample_count": len(scored),
        "sample_count_requested": len(samples),
        "sample_failures": failures,
        "samples": scored,
    }


def compare_walking_routes(origin, destination, visit_dt=None):
    """Get up to three Google walking routes and estimate risk at sampled route points."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_ROUTES_API_KEY")
    if not api_key:
        raise RoutesProviderError(
            "Google Routes API key is missing. Add GOOGLE_MAPS_API_KEY to the project-root .env file."
        )

    cache_key = (
        round(origin["lat"], 5),
        round(origin["lng"], 5),
        round(destination["lat"], 5),
        round(destination["lng"], 5),
        visit_dt.isoformat(timespec="minutes") if visit_dt else "now",
    )
    cached = ROUTE_CACHE.get(("routes",) + cache_key)
    if cached is not None:
        return cached

    payload = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin["lat"],
                    "longitude": origin["lng"],
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination["lat"],
                    "longitude": destination["lng"],
                }
            }
        },
        "travelMode": "WALK",
        "computeAlternativeRoutes": True,
        "languageCode": "en",
        "units": "METRIC",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "routes.distanceMeters,routes.duration,"
            "routes.polyline.encodedPolyline,routes.routeLabels"
        ),
    }

    try:
        print("[ROUTES DEBUG] Calling Google Routes API", flush=True)
        response = requests.post(
            GOOGLE_ROUTES_URL,
            json=payload,
            headers=headers,
            timeout=20,
        )
        print(
            f"[ROUTES DEBUG] Google responded: HTTP {response.status_code}",
            flush=True,
        )
    except requests.RequestException as exc:
        raise RoutesProviderError(
            "Could not connect to Google Routes API. Please retry."
        ) from exc

    if response.status_code in (401, 403):
        raise RoutesProviderError(
            "Google Routes API rejected the key. Check that Routes API is enabled and the key has permission."
        )
    if response.status_code == 429:
        raise RoutesProviderError(
            "Google Routes API rate limit reached. Please wait and retry."
        )
    if not response.ok:
        raise RoutesProviderError(
            f"Google Routes API request failed (HTTP {response.status_code})."
        )

    try:
        raw_routes = response.json().get("routes", [])[:MAX_ROUTES]
    except ValueError as exc:
        raise RoutesProviderError(
            "Google Routes API returned an invalid response."
        ) from exc

    if not raw_routes:
        raise RoutesProviderError(
            "Google could not find a walking route between those points."
        )

    # Scoped to this API request; a later request can try live scoring again.
    live_scoring_failed = [False]
    results = []

    for index, route in enumerate(raw_routes):
        try:
            results.append(
                _compare_route(route, index, visit_dt, live_scoring_failed)
            )
        except (ValueError, RoutesProviderError):
            # Do not return a route whose geometry cannot be processed.
            continue

    if not results:
        raise RoutesProviderError(
            "Routes were found, but their geometry could not be processed."
        )

    comparable = [
        route for route in results
        if route["estimated_risk_score"] is not None
    ]
    safest_id = (
        min(comparable, key=lambda route: route["estimated_risk_score"])["id"]
        if comparable
        else None
    )

    for route in results:
        route["safest_estimate"] = route["id"] == safest_id

    output = {
        "origin": origin,
        "destination": destination,
        "travel_mode": "WALK",
        "visit_time_local": (
            visit_dt.isoformat(timespec="minutes") if visit_dt else None
        ),
        "routes": results,
        "safest_estimate_route_id": safest_id,
        "risk_method": f"Mean of up to {SAMPLES_PER_ROUTE} sampled point estimates per route",
        "limitations": [
            "Risk scores are model estimates, not guarantees of personal safety.",
            "The model was trained on Chicago data; confidence may be lower outside Chicago.",
            "Only a few points are sampled along each route; conditions between samples may differ.",
            "Historical incident data is available only where the backend has matching local records.",
        ],
    }
    ROUTE_CACHE.set(("routes",) + cache_key, output)
    return output
