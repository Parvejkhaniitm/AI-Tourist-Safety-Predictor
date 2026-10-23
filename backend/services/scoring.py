"""Core of /api/analyze: loads both models and combines them into one explained score.

score = 50 + place effect (+ local-record effect where available) + time effect + weather effect

Every term is in score points, so the factor cards always add up to the score (before clipping to 0-100).
"""
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from common import MODELS, solar_elevation, to_baseline_score
from osm_features import FEATURE_COLUMNS, get_features_live

from . import explain
from .cache import TTLCache
from .weather import get_local_context

TRAINING_CENTER = (41.8781, -87.6298)
START = 50.0
LOCAL_WEIGHT = 0.7           # share of the place effect taken from real local records when they exist
LOCAL_MATCH_M = 450          # a record cell counts as "here" within this distance
TIME_GROUP = ["hour", "dow", "is_weekend", "is_holiday", "sun_elevation"]
WEATHER_GROUP = ["temp_c", "precip_mm", "snowfall_cm", "wind_kmh", "cloud_pct"]
DISCLAIMER = ("Scores are estimates from a model trained on one region and live public data. "
              "They do not guarantee personal safety.")

_places_cache = TTLCache(ttl=900, namespace="osm_places")
_places_failure_cache = TTLCache(ttl=10, namespace="osm_places_failure")
_analysis_cache = TTLCache(ttl=300, maxsize=1000, namespace="analysis_results_v4")
_holiday_cache = {}
_models = {}


class UpstreamError(Exception):
    """A required outside service (nearby-places lookup) failed."""


def load_models():
    if not _models:
        try:
            _models["temporal"] = joblib.load(MODELS / "temporal_model.joblib")
            _models["spatial"] = joblib.load(MODELS / "spatial_model.joblib")
        except FileNotFoundError as e:
            raise RuntimeError(f"Model file missing ({e.filename}). Run train_temporal.py and "
                               "train_spatial.py first.") from e
    return _models["temporal"], _models["spatial"]


def models_info():
    tp, sp = load_models()
    return {"temporal_mae": round(tp["metrics"]["mae"], 3), "temporal_r2": round(tp["metrics"]["r2"], 3),
            "spatial_model": sp["name"], "spatial_cv_mae_points": round(sp["cv_mae"], 1),
            "spatial_cv_r2": round(sp["cv_r2"], 3)}


# ---------------- helpers ----------------
def haversine_m(lat1, lng1, lat2, lng2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = (np.sin((p2 - p1) / 2) ** 2
         + np.cos(p1) * np.cos(p2) * np.sin(np.radians(np.asarray(lng2) - lng1) / 2) ** 2)
    return 2 * 6371000.0 * np.arcsin(np.sqrt(a))


def is_us_holiday(lat, lng, dt):
    """Holiday flag was learned from US federal holidays, so only apply it inside the US."""
    if not (24 <= lat <= 50 and -125 <= lng <= -66):
        return 0
    if dt.year not in _holiday_cache:
        _holiday_cache[dt.year] = set(USFederalHolidayCalendar()
                                      .holidays(f"{dt.year}-01-01", f"{dt.year}-12-31").date)
    return int(dt.date() in _holiday_cache[dt.year])


def get_places(lat, lng, fast=False):
    key = (round(lat, 3), round(lng, 3))
    hit = _places_cache.get(key)
    if hit is not None:
        return hit
    if _places_failure_cache.get(key):
        raise UpstreamError("Nearby map data is temporarily unavailable.")
    try:
        places = get_features_live(lat, lng, fast=fast)
    except Exception as e:
        _places_failure_cache.set(key, True)
        print(f"[SCORING] Nearby-place lookup failed: {type(e).__name__}: {e}", flush=True)
        raise UpstreamError(
            f"Nearby-place lookup failed after mirror retries ({type(e).__name__}: {e})."
        ) from e
    _places_cache.set(key, places)
    return places


def nearest_record(cells, lat, lng):
    d = haversine_m(lat, lng, cells["lat"].to_numpy(), cells["lng"].to_numpy())
    i = int(np.argmin(d))
    return cells.iloc[i].to_dict() if d[i] <= LOCAL_MATCH_M else None


HOUR_CURVE = [0.10, 0.06, 0.04, 0.03, 0.04, 0.10, 0.30, 0.55, 0.75, 0.85, 0.95, 1.0,
              1.0, 1.0, 0.95, 0.95, 0.95, 1.0, 0.95, 0.85, 0.70, 0.50, 0.30, 0.18]


def crowd_estimate(places, local_dt):
    """Context-only estimate: how built-up the area is x how active people usually are at this hour."""
    density = min(1.0, math.log1p(places["poi_total"]) / math.log1p(100))
    leisure = places["bars"] + places["food"] + places["attractions"] + places["lodging"]
    leisure_share = leisure / max(places["poi_total"], 1)
    weekend = local_dt.weekday() >= 5
    wk = (1.2 if leisure_share > 0.5 else 1.0) if weekend else 1.0
    index = 100 * density * HOUR_CURVE[local_dt.hour] * wk
    level = "Busy" if index >= 45 else "Moderate" if index >= 20 else "Quiet"
    basis = (f"Based on how built-up the area is and typical activity at {local_dt:%H:%M}"
             f"{' on a weekend' if weekend else ''}.")
    return {"level": level, "index": round(min(index, 100), 1), "basis": basis}


def confidence(places, iso_outlier, dist_training_km, weather_ok, has_local):
    score, reasons = 100, []
    if dist_training_km > 30:
        score -= 60
        reasons.append("This place is outside the region represented in the model's training data.")
    if iso_outlier:
        score -= 30
        reasons.append("The surroundings look unusual compared with the places the model learned from.")
    if not weather_ok:
        score -= 15
        reasons.append("Weather data was unavailable.")
    if places is None:
        score -= 20
        reasons.append("Nearby OpenStreetMap data was unavailable, so location features were not scored.")
    elif places["poi_total"] == 0 and sum(places[c] for c in FEATURE_COLUMNS if c != "poi_total") == 0:
        score -= 20
        reasons.append("Very little map data was found nearby.")
    elif places["poi_total"] < 3:
        score -= 8
        reasons.append("Little map data was found nearby.")
    if has_local:
        reasons.append("Real local incident records were available for this area.")
    label = "High" if score >= 75 else "Medium" if score >= 45 else "Low"
    return {"label": label, "reasons": reasons or ["Conditions are close to the data the model learned from."]}


def level_of(score):
    return ("Safe", "0-39") if score < 40 else ("Moderate", "40-69") if score < 70 else ("Risky", "70-100")


# ---------------- main entry ----------------
def analyze(lat, lng, name, local_dt=None, fast=False, force_refresh=False):
    # Whole-response cache makes returning to an already analyzed place cheap.
    # Default analyses are keyed by UTC hour so a result cannot bleed across
    # a local-time/hour boundary; explicitly requested visit times use the minute.
    visit_key = (
        local_dt.isoformat(timespec="minutes")
        if local_dt else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
    )
    cache_key = (round(lat, 5), round(lng, 5), str(name).strip().casefold(), visit_key)
    if not force_refresh:
        cached_result = _analysis_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    tp, sp = load_models()
    dist_km = float(haversine_m(lat, lng, *TRAINING_CENTER)) / 1000
    outside_training_area = dist_km > 30
    # Weather and OSM do not depend on each other: overlap their network wait.
    with ThreadPoolExecutor(max_workers=2) as pool:
        weather_future = pool.submit(get_local_context, lat, lng, local_dt)
        places_future = pool.submit(get_places, lat, lng, fast=fast)
        ctx = weather_future.result()
        try:
            places = places_future.result()
        except UpstreamError:
            # Keep analysis usable when Overpass is temporarily unreachable, but
            # never substitute invented POI counts or describe the map as observed.
            places = None
    ldt, weather = ctx["local_dt"], ctx["weather"]

    # --- "where": place baseline ---
    model_places = places if places is not None else sp["median"]
    Xs = pd.DataFrame([{c: model_places[c] for c in FEATURE_COLUMNS}])[sp["features"]]
    model_base = (
        float(to_baseline_score(sp, float(sp["model"].predict(Xs)[0])))
        if places is not None else START
    )
    # A region-specific model can extrapolate to extreme values elsewhere. Blend
    # remote estimates toward neutral instead of clipping them to a misleading 0/100.
    if outside_training_area:
        model_base = START + (model_base - START) * 0.25
    hist = nearest_record(sp["cells"], lat, lng)
    if hist:
        w_loc = 1 - LOCAL_WEIGHT
        loc_pts = w_loc * (model_base - START)
        hist_pts = LOCAL_WEIGHT * (hist["label"] - START)
    else:
        loc_pts, hist_pts = model_base - START, None
    iso_outlier = int(sp["isolation"].predict(Xs)[0]) == -1 if places is not None else False

    # --- "when": time + weather ---
    sun = float(solar_elevation(lat, lng, pd.DatetimeIndex([ctx["utc_dt"]]))[0])
    row = {"hour": ldt.hour, "dow": ldt.weekday(), "is_weekend": int(ldt.weekday() >= 5),
           "is_holiday": is_us_holiday(lat, lng, ldt), "sun_elevation": sun}
    row.update(weather if weather else {k: tp["feature_median"][k] for k in WEATHER_GROUP})
    X = pd.DataFrame([row])[tp["features"]]
    bg = tp["background"]
    full = float(tp["model"].predict(X)[0])

    def marginal(group):  # average prediction when `group` is replaced by typical (background) values
        Z = pd.concat([X] * len(bg), ignore_index=True)
        Z[group] = bg[group].to_numpy()
        return float(np.mean(tp["model"].predict(Z)))

    scale, ref = tp["scale"], tp["ref_log"]
    if weather:
        weather_pts = scale * (full - marginal(WEATHER_GROUP))
        time_pts = scale * (full - ref) - weather_pts
    else:
        weather_pts, time_pts = None, scale * (marginal(WEATHER_GROUP) - ref)
    # keep the adjustment sensible and the cards additive
    adj = time_pts + (weather_pts or 0.0)
    if abs(adj) > 30:
        f = 30 / abs(adj)
        time_pts, weather_pts = time_pts * f, (weather_pts * f if weather_pts is not None else None)
    if outside_training_area:
        time_pts *= 0.5
        weather_pts = weather_pts * 0.5 if weather_pts is not None else None

    raw_total = START + loc_pts + (hist_pts or 0.0) + time_pts + (weather_pts or 0.0)
    score = int(round(min(100.0, max(0.0, raw_total))))
    level, level_range = level_of(score)

    # --- explanation, confidence ---
    crowd = crowd_estimate(places, ldt) if places is not None else None
    factors = explain.build_factors(
        places=places, loc_pts=loc_pts, hist=hist, hist_pts=hist_pts, time_pts=time_pts,
        weather_pts=weather_pts, local_dt=ldt, sun_elev=sun, is_holiday=row["is_holiday"],
        weather=weather, weather_error=ctx["weather_error"], crowd=crowd)
    conf = confidence(places, iso_outlier, dist_km, weather is not None, hist is not None)
    if outside_training_area:
        conf["reasons"].append("Model effects are reduced outside the region represented in its training data.")

    margin = sp["cv_mae"] * (0.5 if hist else 1.0) * (1.5 if dist_km > 30 else 1.0)
    missing = [f["key"] for f in factors if not f["available"]]
    result = {
        "destination": {"name": name, "lat": lat, "lng": lng},
        "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "visit_time_local": ldt.isoformat(timespec="minutes"),
        "timezone": ctx["timezone"],
        "score": score, "level": level, "level_range": level_range,
        "score_start": START,
        "margin_points": round(margin),
        "confidence": conf,
        "reasons": explain.top_reasons(factors),
        "factors": [{k: v for k, v in f.items() if k != "reason"} for f in factors],
        "missing_factors": missing,
        "factors_used": sum(f["available"] for f in factors if f["key"] != "crowd"),
        "factors_total": sum(f["key"] != "crowd" for f in factors),
        "disclaimer": DISCLAIMER,
    }
    _analysis_cache.set(cache_key, result)
    return result
