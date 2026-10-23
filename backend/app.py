"""SafeRoute AI backend.  Run from the project root:  python backend/app.py"""
import logging
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND / "ml"))
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402
from flask import Flask, jsonify, request  # noqa: E402
from flask_cors import CORS  # noqa: E402

load_dotenv(BACKEND.parent / ".env")

from services.scoring import UpstreamError, analyze, load_models, models_info  # noqa: E402

app = Flask(__name__)
CORS(app)  # lets the Vue dev server (another port) call this API
log = logging.getLogger("saferoute")


def error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


@app.get("/api/health")
def health():
    try:
        return jsonify({"status": "ok", "models": models_info()})
    except RuntimeError as e:
        return error("models_missing", str(e), 500)


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
        return jsonify(analyze(lat, lng, name, local_dt))
    except UpstreamError as e:
        return error("upstream_failure", str(e), 503)
    except RuntimeError as e:
        return error("models_missing", str(e), 500)
    except Exception:
        log.exception("analyze failed")
        return error("internal_error", "Analysis failed unexpectedly. Please try again.", 500)


if __name__ == "__main__":
    load_models()  # fail fast if the models were not trained
    app.run(host="0.0.0.0", port=5000, debug=True)