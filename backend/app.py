"""SafeRoute AI backend.  Run from the project root:  python backend/app.py"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND / "ml"))
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402
from flask import Flask, jsonify, request  # noqa: E402
from flask_cors import CORS  # noqa: E402

load_dotenv(BACKEND / ".env")
load_dotenv(BACKEND.parent / ".env")

from services.scoring import UpstreamError, analyze, load_models, models_info  # noqa: E402
from services.routes import RoutesProviderError, _valid_point, compare_routes  # noqa: E402
from services.geocoding import GeocodingError, reverse_place, search_place  # noqa: E402
from services.cache import cache_backend  # noqa: E402

app = Flask(__name__)
allowed_origins = {
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", ""
    ).split(",")
    if origin.strip()
}
allowed_origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
CORS(app, resources={r"/api/*": {"origins": sorted(allowed_origins)}})
log = logging.getLogger("saferoute")


def error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


@app.get("/api/health")
def health():
    try:
        return jsonify({"status": "ok", "cache": cache_backend(), "models": models_info()})
    except RuntimeError as e:
        return error("models_missing", str(e), 500)


@app.get("/api/destinations")
def destinations():
    return jsonify([
        {"name": name, "lat": lat, "lng": lng}
        for name, lat, lng in (
            ("India Gate", 28.6129, 77.2295),
            ("Red Fort", 28.6562, 77.2410),
            ("Qutub Minar", 28.5245, 77.1855),
            ("Humayun's Tomb", 28.5933, 77.2507),
            ("Lotus Temple", 28.5535, 77.2588),
        )
    ])


@app.get("/api/geocode")
def geocode():
    """Resolve a user-submitted place once (never used for autocomplete)."""
    query = request.args.get("q", "")
    try:
        return jsonify(search_place(query))
    except ValueError as e:
        return error("invalid_input", str(e), 400)
    except LookupError as e:
        return error("not_found", str(e), 404)
    except GeocodingError as e:
        return error("geocoder_unavailable", str(e), 503)


@app.get("/api/reverse-geocode")
def reverse_geocode():
    try:
        lat, lng = float(request.args["lat"]), float(request.args["lng"])
    except (KeyError, TypeError, ValueError):
        return error("invalid_input", "lat and lng are required numbers.", 400)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return error("invalid_input", "lat must be -90..90 and lng must be -180..180.", 400)
    try:
        return jsonify(reverse_place(lat, lng))
    except LookupError as e:
        return error("not_found", str(e), 404)
    except GeocodingError as e:
        return error("geocoder_unavailable", str(e), 503)


@app.post("/api/analyze")
def api_analyze():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("invalid_input", "Send a JSON body like {\"lat\": 28.61, \"lng\": 77.23}.", 400)
    try:
        lat, lng = float(body["lat"]), float(body["lng"])
    except (KeyError, TypeError, ValueError):
        return error("invalid_input", "lat and lng are required numbers.", 400)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return error("invalid_input", "lat must be -90..90 and lng must be -180..180.", 400)

    local_dt = None
    if body.get("datetime"):
        try:  # visit time as local time at the destination, e.g. "2026-10-24T21:30"
            local_dt = datetime.fromisoformat(str(body["datetime"]).replace("Z", "")).replace(tzinfo=None)
        except ValueError:
            return error("invalid_input", "datetime must look like 2026-10-24T21:30.", 400)

    name = str(body.get("name") or f"{lat:.4f}, {lng:.4f}").strip()[:120]
    try:
        return jsonify(analyze(
            lat,
            lng,
            name,
            local_dt,
            fast=True,
            force_refresh=bool(body.get("force_refresh", False)),
        ))
    except UpstreamError as e:
        return error("upstream_failure", str(e), 503)
    except RuntimeError as e:
        return error("models_missing", str(e), 500)
    except Exception:
        log.exception("analyze failed")
        return error("internal_error", "Analysis failed unexpectedly. Please try again.", 500)


@app.post("/api/routes")
def api_routes():
    """Return driving route alternatives plus model-estimated risk comparisons."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("invalid_input", "Send origin and destination objects with lat and lng.", 400)

    try:
        origin = _valid_point(body.get("origin"), "origin")
        destination = _valid_point(body.get("destination"), "destination")
    except ValueError as e:
        return error("invalid_input", str(e), 400)

    local_dt = None
    if body.get("datetime"):
        try:
            local_dt = datetime.fromisoformat(str(body["datetime"]).replace("Z", "")).replace(tzinfo=None)
        except ValueError:
            return error("invalid_input", "datetime must look like 2026-10-24T21:30.", 400)

    try:
        result = compare_routes(origin, destination, local_dt)
        return jsonify(result)
    except RoutesProviderError as e:
        return error("routes_unavailable", str(e), 503)
    except UpstreamError as e:
        return error("upstream_failure", str(e), 503)
    except RuntimeError as e:
        return error("models_missing", str(e), 500)
    except Exception:
        log.exception("route comparison failed")
        return error("internal_error", "Route comparison failed unexpectedly. Please try again.", 500)


if __name__ == "__main__":
    load_models()  # fail fast if the models were not trained
    app.run(host="127.0.0.1", port=5000, debug=True)
