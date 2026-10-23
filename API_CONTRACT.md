# SafeRoute AI API contract

The Vue frontend and active Flask API use the same JSON contracts below. All endpoints use the `/api` prefix. Errors return `{ "error": { "code": "...", "message": "..." } }`.

## Active endpoints

| Endpoint | Request | Response |
|---|---|---|
| `GET /api/health` | None | `{ status, models }`; loads both bundled model artifacts |
| `GET /api/destinations` | None | Five quick-start suggestions; users can also search for other places |
| `GET /api/geocode?q=...` | User-submitted place query | Coordinates and a display label; called on submit, never autocomplete |
| `GET /api/reverse-geocode?lat=...&lng=...` | Browser location | Nearby area label using rounded coordinates |
| `POST /api/analyze` | `{ lat, lng, name?, datetime? }` | Location risk estimate, confidence, explanations, factors, and caveats |
| `POST /api/routes` | `{ origin: { lat, lng, name? }, destination: { lat, lng, name? }, datetime? }` | Road geometry, distance/time, and sampled model risk estimates |

Scores are 0–100 **risk estimates**: a lower score means lower estimated risk. They are not emergency guidance or a guarantee of safety.

## Analysis response

`POST /api/analyze` returns `destination` (`name`, `lat`, `lng`), `analyzed_at`, `visit_time_local`, `timezone`, `score`, `level`, `level_range`, `confidence` (`label`, `reasons`), `reasons`, `factors`, `missing_factors`, `factors_used`, `factors_total`, and `disclaimer`.

Each factor includes `key`, `title`, `text`, `impact`, `impact_label`, `points`, `data_label`, and `available`. When nearby map data is unavailable, the location and crowd factors are marked unavailable and excluded rather than filled with fabricated counts. The analysis can still return a lower-confidence estimate from the time/weather signal and any local history that exists.

## Route response

The route response contains named `origin` and `destination`, `travel_mode`, `route_provider`, `routes`, `safest_estimate_route_id`, `risk_method`, and `limitations`. Each route has `id`, `distance_meters`, `duration_seconds`, `path` (`[{ lat, lng }]`), `estimated_risk_score` (nullable), `estimated_risk_level`, `confidence`, and sampling details. A missing risk estimate does not hide a route's actual distance, duration, or geometry.

When `GOOGLE_MAPS_API_KEY` or `GOOGLE_ROUTES_API_KEY` is configured, Google Routes is tried first; otherwise OSRM is used. If the first provider returns only one road, a Valhalla OpenStreetMap router is queried for alternatives. The frontend displays every distinct returned road geometry on an OpenStreetMap Leaflet map and offers a separate Google Maps directions link. Public routing providers can still return just one road when they cannot find a qualifying alternate.

## Model and data limits

The bundled Random Forest/XGBoost pipeline has limited geographic training coverage. Estimates outside its training region have low confidence when matching local historical records are unavailable. Weather comes from Open-Meteo; nearby place features come from OpenStreetMap Overpass; road directions come from Google Routes or OpenStreetMap routing. Provider outages are shown as unavailable data. Crowd level is contextual and does not change the score. Routing services may return fewer alternatives than requested; only actual returned road paths are displayed.

Place lookups use OpenStreetMap Nominatim on user submit only, cache results, and limit requests to one per second. Current-location naming rounds coordinates before lookup. The UI discloses this location use to the user.

Place lookups use OpenStreetMap Nominatim on user submit only, cache results, and limit requests to one per second. Current-location naming rounds coordinates before lookup. The UI discloses this location use to the user.

The active app is `backend/app.py` and its services under `backend/services/` and `backend/ml/`. The separate `backend/app/` package contains an earlier auth/database scaffold and is not wired into these active API routes. Authentication, saved analysis history, and account endpoints are not available in the current running service.

## Local setup

From the repository root:

```powershell
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
backend/.venv/Scripts/python.exe backend/app.py
```

In another terminal, run `npm install` and `npm run dev`. The root `.env` should set `VITE_API_MODE=live` and leave `VITE_API_BASE_URL` empty to use Vite's proxy to `http://127.0.0.1:5000`. Use `VITE_API_MODE=mock` to run the frontend with local sample data instead.
