"""Google Routes API integration and sampled risk comparison for walking routes."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

from .scoring import UpstreamError, analyze, load_models, nearest_record
from .cache import TTLCache

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTE_RESULT_CACHE = TTLCache(ttl=900, maxsize=100, namespace="route_results")
ROUTE_SAMPLE_CACHE = TTLCache(ttl=900, maxsize=1000, namespace="route_risk_samples")
MAX_ROUTES = 4
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


def decode_polyline(encoded, precision=5):
    """Decode an encoded polyline into [{lat, lng}, ...]."""
    points, index, lat, lng = [], 0, 0, 0
    factor = 10 ** precision
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
        points.append({"lat": lat / factor, "lng": lng / factor})
    return points


def _valhalla_routes(origin, destination):
    """Ask a second OSM router for alternatives when the first has only one."""
    response = requests.post(
        "https://valhalla1.openstreetmap.de/route",
        json={
            "locations": [
                {"lat": origin["lat"], "lon": origin["lng"]},
                {"lat": destination["lat"], "lon": destination["lng"]},
            ],
            "costing": "auto",
            "alternates": 2,
            "format": "json",
            "shape_format": "polyline6",
            "units": "kilometers",
            "directions_type": "none",
        },
        headers={"X-Client-Id": "SafeRouteAI demo", "User-Agent": "SafeRouteAI/1.0"},
        timeout=4,
    )
    response.raise_for_status()
    payload = response.json()
    trips = [payload.get("trip")]
    trips.extend(item.get("trip") for item in payload.get("alternates", []) if isinstance(item, dict))
    routes = []
    for trip in trips:
        if not isinstance(trip, dict):
            continue
        legs = trip.get("legs") or []
        summary = trip.get("summary") or {}
        if not legs or not legs[0].get("shape"):
            continue
        path = decode_polyline(legs[0]["shape"], precision=6)
        if len(path) < 2:
            continue
        routes.append({
            "label": "OpenStreetMap alternative",
            "distance_meters": float(summary.get("length", 0)) * 1000,
            "duration_seconds": float(summary.get("time", 0)),
            "path": path,
        })
    return routes


def _distinct_routes(routes):
    """Drop near-identical duplicates returned by independent routing engines."""
    unique = []
    for candidate in routes:
        distance = candidate.get("distance_meters") or 0
        path = candidate.get("path") or []
        midpoint = path[len(path) // 2] if path else None
        duplicate = False
        for existing in unique:
            other_distance = existing.get("distance_meters") or 0
            other_path = existing.get("path") or []
            other_midpoint = other_path[len(other_path) // 2] if other_path else None
            distance_close = abs(distance - other_distance) < max(750, distance * 0.015)
            midpoint_close = midpoint and other_midpoint and (
                abs(midpoint["lat"] - other_midpoint["lat"]) < 0.008
                and abs(midpoint["lng"] - other_midpoint["lng"]) < 0.008
            )
            if distance_close and midpoint_close:
                duplicate = True
                break
        if not duplicate:
            unique.append(candidate)
    return unique


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
        "reasons": [
            "This estimate uses the nearest available historical grid cell only.",
            "Live surroundings, time, and weather effects were unavailable for this route sample.",
        ],
    }


def _score_sample(point, visit_dt, live_scoring_failed=None):
    """Try live scoring unless it already failed for this request; then use history."""

    key = (
        round(point["lat"], 4),
        round(point["lng"], 4),
        visit_dt.isoformat(timespec="minutes") if visit_dt else "now",
    )

    cached = ROUTE_SAMPLE_CACHE.get(key)
    if cached is not None:
        return cached

    # Once live scoring fails for this comparison request, skip repeat network
    # attempts but still score each route independently from the historical grid.
    skip_live = live_scoring_failed is not None and live_scoring_failed[0]

    if not skip_live:
        try:
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
                "reasons": list(dict.fromkeys(
                    result.get("reasons", [])
                    + result.get("confidence", {}).get("reasons", [])
                )),
            }

        except UpstreamError:
            if live_scoring_failed is not None:
                live_scoring_failed[0] = True
            sample = _historical_sample(point)
    else:
        sample = _historical_sample(point)

    ROUTE_SAMPLE_CACHE.set(key, sample)
    return sample


def _compare_route(route, index, visit_dt, live_scoring_failed=None):
    encoded = route.get("polyline", {}).get("encodedPolyline")
    if route.get("path"):
        path = route["path"]
    elif encoded:
        path = decode_polyline(encoded)
    else:
        raise RoutesProviderError("The route provider returned no usable geometry.")
    samples = _route_samples(path)
    scored, failures = [], 0

    for point in samples:
        try:
            scored.append(_score_sample(point, visit_dt, live_scoring_failed))
        except (UpstreamError, RuntimeError, requests.RequestException) as exc:
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

    reasons = list(dict.fromkeys(
        reason for item in scored for reason in item.get("reasons", [])
    ))
    if risk is None:
        explanation = "A route risk estimate could not be calculated from the available data."
    else:
        explanation = (
            f"Estimated route risk is {risk}/100, based on {len(scored)} sampled point"
            f"{'s' if len(scored) != 1 else ''} ({confidence.lower()} confidence). "
            + (" ".join(reasons[:2]) if reasons else "No route-specific risk signals were available.")
        )

    return {
        "id": f"route-{index + 1}",
        "label": route.get("label") or ("Recommended route" if index == 0 else f"Alternative {index}"),
        "distance_meters": route.get("distanceMeters", route.get("distance_meters")),
        "duration_seconds": _duration_seconds(route.get("duration")) if route.get("duration") is not None else route.get("duration_seconds"),
        "polyline": encoded,
        "path": path,
        "estimated_risk_score": risk,
        "estimated_risk_level": level,
        "confidence": confidence,
        "sample_count": len(scored),
        "sample_count_requested": len(samples),
        "sample_failures": failures,
        "samples": scored,
        "risk_reasons": reasons[:3],
        "risk_explanation": explanation,
    }


def compare_routes(origin, destination, visit_dt=None):
    """Get road alternatives and estimate risk at sampled route points."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_ROUTES_API_KEY")
    cache_key = (
        round(origin["lat"], 5),
        round(origin["lng"], 5),
        round(destination["lat"], 5),
        round(destination["lng"], 5),
        origin["name"].casefold(),
        destination["name"].casefold(),
        visit_dt.isoformat(timespec="minutes") if visit_dt else "now",
    )
    cached = ROUTE_RESULT_CACHE.get(cache_key)
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
        "travelMode": "DRIVE",
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

    raw_routes = []
    provider = "OSRM"
    if api_key:
        try:
            response = requests.post(GOOGLE_ROUTES_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            raw_routes = response.json().get("routes", [])[:MAX_ROUTES]
            provider = "Google"
        except (requests.RequestException, ValueError) as exc:
            print(f"[ROUTES] Google unavailable; trying OSRM ({type(exc).__name__}).", flush=True)

    if not raw_routes:
        try:
            coordinates = f"{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
            response = requests.get(
                f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
                params={"alternatives": "3", "overview": "full", "geometries": "geojson"},
                headers={"User-Agent": "SafeRouteAI/1.0 (route comparison demo)"},
                timeout=8,
            )
            response.raise_for_status()
            payload_osrm = response.json()
            if payload_osrm.get("code") != "Ok":
                raise RoutesProviderError("No drivable route was found between those points.")
            raw_routes = [
                {
                    "label": "OSRM route",
                    "distance_meters": route.get("distance"),
                    "duration_seconds": route.get("duration"),
                    "path": [{"lat": lat, "lng": lng} for lng, lat in route.get("geometry", {}).get("coordinates", [])],
                }
                for route in payload_osrm.get("routes", [])[:MAX_ROUTES]
            ]
        except (requests.RequestException, ValueError) as exc:
            raise RoutesProviderError("Could not get directions. Please retry in a moment.") from exc

    if len(raw_routes) < 2:
        try:
            extra_routes = _valhalla_routes(origin, destination)
            raw_routes = _distinct_routes(raw_routes + extra_routes)
            if len(raw_routes) > 1:
                provider = f"{provider} + OpenStreetMap alternatives"
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            print(f"[ROUTES] Alternate router unavailable ({type(exc).__name__}).", flush=True)

    if not raw_routes:
        raise RoutesProviderError(
            "No driving route was found between those points."
        )

    # Load the models before concurrent scoring so workers don't race model init.
    load_models()
    # Route samples are independent. Score at most two at a time to reduce cold
    # request latency without flooding the public map/weather providers.
    results_by_index = []
    with ThreadPoolExecutor(max_workers=min(2, len(raw_routes))) as pool:
        futures = {
            pool.submit(_compare_route, route, index, visit_dt): index
            for index, route in enumerate(raw_routes)
        }
        for future, index in futures.items():
            try:
                results_by_index.append((index, future.result()))
            except (ValueError, RoutesProviderError):
                # Do not return a route whose geometry cannot be processed.
                continue
    results = [result for _, result in sorted(results_by_index, key=lambda item: item[0])]

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
        "travel_mode": "DRIVE",
        "route_provider": provider,
        "visit_time_local": (
            visit_dt.isoformat(timespec="minutes") if visit_dt else None
        ),
        "routes": results,
        "safest_estimate_route_id": safest_id,
        "risk_method": f"Mean of up to {SAMPLES_PER_ROUTE} sampled point estimates per route",
        "limitations": [
            "Risk scores are model estimates, not guarantees of personal safety.",
            "The model has strongest coverage in its training region; confidence may be lower elsewhere.",
            "Only a few points are sampled along each route; conditions between samples may differ.",
            "Historical incident data is available only where the backend has matching local records.",
        ],
    }
    ROUTE_RESULT_CACHE.set(cache_key, output)
    return output
