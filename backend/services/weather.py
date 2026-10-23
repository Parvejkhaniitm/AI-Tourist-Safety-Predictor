"""Live weather + local time for any place on Earth, from Open-Meteo (free, no key)."""
from datetime import datetime, timedelta, timezone

import requests

from .cache import TTLCache

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,precipitation,snowfall,wind_speed_10m,cloud_cover"
_cache = TTLCache(ttl=900)


def _load(lat, lng):
    key = (round(lat, 2), round(lng, 2))
    hit = _cache.get(key)
    if hit:
        return hit
    r = requests.get(URL, timeout=4, params={
        "latitude": lat, "longitude": lng, "hourly": HOURLY,
        "timezone": "auto", "past_days": 7, "forecast_days": 16,
    })
    r.raise_for_status()
    data = r.json()
    _cache.set(key, data)
    return data


def get_local_context(lat, lng, local_dt=None):
    """Returns the visit time (local + UTC), timezone and the weather for that hour.

    local_dt: naive datetime in the destination's local time, or None for "now".
    weather is None (with weather_error set) when the service can't provide it.
    """
    data, error = None, None
    try:
        data = _load(lat, lng)
        offset = int(data["utc_offset_seconds"])
        tz_name = data.get("timezone", "")
    except Exception as e:  # network, bad JSON, missing keys ...
        offset = round(lng / 15) * 3600
        tz_name = f"UTC{offset // 3600:+d} (approximate)"
        error = f"weather service unavailable ({type(e).__name__})"

    if local_dt is None:
        local_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=offset)
    local_dt = local_dt.replace(minute=0, second=0, microsecond=0)
    utc_dt = local_dt - timedelta(seconds=offset)

    weather = None
    if data is not None:
        h = data["hourly"]
        try:
            i = h["time"].index(local_dt.strftime("%Y-%m-%dT%H:%M"))
        except ValueError:
            error = "visit time is outside the weather forecast window (past 7 to next 16 days)"
        else:
            temp, precip, wind = h["temperature_2m"][i], h["precipitation"][i], h["wind_speed_10m"][i]
            if None in (temp, precip, wind):
                error = "weather data incomplete for that hour"
            else:
                snow, cloud = h["snowfall"][i], h["cloud_cover"][i]
                weather = {
                    "temp_c": float(temp), "precip_mm": float(precip),
                    "snowfall_cm": float(snow or 0.0), "wind_kmh": float(wind),
                    "cloud_pct": float(cloud if cloud is not None else 50.0),
                }
    return {"local_dt": local_dt, "utc_dt": utc_dt, "timezone": tz_name,
            "utc_offset_s": offset, "weather": weather, "weather_error": error}