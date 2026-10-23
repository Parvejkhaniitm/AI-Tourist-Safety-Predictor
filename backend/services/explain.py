"""Turns numbers into the five factor cards and the plain-English reasons."""

NAMES = {
    "shops": "shops", "food": "restaurants and cafes", "bars": "bars and pubs",
    "rail_stations": "transit stations", "bus_stops": "bus stops", "parks": "parks",
    "lodging": "hotels", "attractions": "attractions", "schools": "schools",
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def impact(points, mild, strong):
    """-> (key, label). Positive points raise risk."""
    if points is None:
        return "unavailable", "Unavailable"
    a = abs(points)
    if a < mild:
        return "neutral", "Neutral"
    up = points > 0
    if a < strong:
        return ("raises", "Raises risk slightly") if up else ("lowers", "Lowers risk slightly")
    return ("raises", "Raises risk") if up else ("lowers", "Lowers risk")


def _adv(points, strong):
    """'slightly ' for small effects so reasons don't overstate a 2-point nudge."""
    return "slightly " if abs(points) < strong else ""


def _card(key, title, text, points, mild, strong, data_label, reason, available=True):
    ikey, ilabel = impact(points if available else None, mild, strong)
    return {
        "key": key, "title": title, "text": text, "impact": ikey, "impact_label": ilabel,
        "points": None if points is None else round(points, 1),
        "data_label": data_label, "available": available, "reason": reason,
    }


def describe_surroundings(places):
    ranked = sorted(((places[k], k) for k in NAMES if places.get(k, 0) > 0), reverse=True)[:3]
    total = places["poi_total"]
    if not ranked:
        return "Very little is mapped around this point (open land, water, or sparse map data)."
    parts = ", ".join(f"{n} {NAMES[k]}" for n, k in ranked)
    kind = ("Dense commercial area" if total >= 40 else
            "Moderately busy area" if total >= 10 else "Quiet area")
    return f"{kind}: {parts} within 400 m."


def sun_phase(elev):
    return "daylight" if elev > 6 else "twilight" if elev > -6 else "night"


def describe_weather(w):
    p = w["precip_mm"]
    rain = ("dry" if p < 0.1 else "light drizzle" if p < 0.5 else "rain" if p < 2.5 else "heavy rain")
    snow = ", snow" if w["snowfall_cm"] > 0 else ""
    return f"{w['temp_c']:.0f}\u00b0C, {rain}{snow}, wind {w['wind_kmh']:.0f} km/h."


def build_factors(*, places, loc_pts, hist, hist_pts, time_pts, weather_pts, local_dt, sun_elev,
                  is_holiday, weather, weather_error, crowd):
    factors = []

    d = "raise" if loc_pts > 0 else "lower"
    factors.append(_card(
        "location", "Location", describe_surroundings(places), loc_pts, 4, 12,
        "OpenStreetMap places within 400 m (live)",
        f"The surroundings {_adv(loc_pts, 12)}{d} the estimate by about {abs(loc_pts):.0f} points."))

    day = DAYS[local_dt.weekday()]
    phase = sun_phase(sun_elev)
    holiday = " Public holiday." if is_holiday else ""
    d = "raises" if time_pts > 0 else "lowers"
    factors.append(_card(
        "time", "Time and Day", f"{day}, {local_dt:%H:%M} local time. {phase.capitalize()}.{holiday}",
        time_pts, 2, 6, "From the selected visit time",
        f"{day} {local_dt:%H:%M} ({phase}) {_adv(time_pts, 6)}{d} the estimate by about {abs(time_pts):.0f} points."))

    factors.append(_card(
        "crowd", "Crowd Density", f"{crowd['level']} (estimate). {crowd['basis']}", 0.0, 99, 99,
        "Estimated from typical patterns, not live; context only, not used in the score",
        "Crowd level is shown for context and does not change the score."))

    if weather is not None:
        d = "raises" if weather_pts > 0 else "lowers"
        factors.append(_card(
            "weather", "Weather", describe_weather(weather), weather_pts, 1, 4,
            "Open-Meteo (live forecast)",
            f"The weather {_adv(weather_pts, 4)}{d} the estimate by about {abs(weather_pts):.0f} points."))
    else:
        factors.append(_card(
            "weather", "Weather: data unavailable",
            f"{weather_error or 'No weather data'}, so this factor is left out.", None, 1, 4,
            "Open-Meteo", "Weather was not available.", available=False))

    if hist is not None:
        d = "raise" if hist_pts > 0 else "lower"
        factors.append(_card(
            "history", "Historical Incidents",
            f"About {int(hist['total_crimes']):,} recorded incidents in this ~500 m area over the last 2 years "
            f"(relative risk rank {hist['label']:.0f}/100).", hist_pts, 4, 12,
            "Chicago open data records",
            f"Past incident records {_adv(hist_pts, 12)}{d} the estimate by about {abs(hist_pts):.0f} points."))
    else:
        factors.append(_card(
            "history", "Historical Incidents: no local records",
            "No incident records are available for this area, so the estimate relies on patterns "
            "learned from Chicago.", None, 4, 12, "Chicago open data (not available here)",
            "No local incident records were available.", available=False))
    return factors


def top_reasons(factors, n=3):
    scored = [f for f in factors if f["available"] and f["key"] != "crowd"]
    scored.sort(key=lambda f: abs(f["points"] or 0), reverse=True)
    return [f["reason"] for f in scored[:n]]