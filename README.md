# SafeRoute AI

Vue 3 + Vite frontend for a destination risk analysis and route comparison demo. The frontend supports local mock mode and a Flask REST API backend.

## Frontend

```sh
npm install
npm run dev
```

Set `VITE_API_MODE=live` in the root `.env` to connect the UI to Flask; leave `VITE_API_BASE_URL` empty for the Vite proxy to `http://127.0.0.1:5000`. Mock mode is available with `VITE_API_MODE=mock`.

## Backend

See [API_CONTRACT.md](./API_CONTRACT.md) for the API schemas and current model limits. The ML-backed Flask service uses the trained models and services under `backend/`; install the root `requirements.txt` into its environment:

```powershell
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
backend/.venv/Scripts/python.exe backend/app.py
```

In a second terminal, run `npm install` and `npm run dev`. Route comparison uses Google Routes when a `GOOGLE_MAPS_API_KEY` is configured, with OpenStreetMap's OSRM and Valhalla routers as fallbacks for road geometry and alternatives. Place lookup runs only after a search is submitted and uses OpenStreetMap Nominatim with caching and rate limiting; current-location names use rounded coordinates. Weather and nearby-place features also use live external services. The bundled risk models have limited geographic coverage, so estimates outside their training region have low confidence and are not verified local safety reports or a guarantee of personal safety. Routing providers can return fewer alternatives than requested when the road network has no qualifying alternate path.

### Optional Redis cache

The backend uses Redis for shared cache entries when `REDIS_URL` is configured. Cached responses are reused across requests and Flask workers; expiry is automatic. Without Redis, the same cache API falls back to bounded process memory, so the application still runs. Redis entries contain public weather/map responses, geocoded destinations, and route results (including coordinates); use a trusted, access-controlled Redis instance and do not expose Redis directly to the internet.

For local development, start the included Redis service:

```powershell
docker compose -f compose.redis.yml up -d
```

Copy `backend/.env.example` to `backend/.env` (or set the environment variable in your shell) and set `REDIS_URL=redis://localhost:6379/0`. Install the newly added Python dependency with `backend/.venv/Scripts/python.exe -m pip install -r requirements.txt`, then restart Flask. `GET /api/health` reports `"cache": "redis"` when connected, otherwise `"cache": "memory"`. The local Redis container binds only to localhost and persists its data in a Docker volume.

Cache lifetimes are tuned by data type: geocoding labels 24 hours, weather forecasts 15 minutes, nearby OSM features 15 minutes, sampled route risk 15 minutes, and complete route comparisons 15 minutes. Successful route results are also stored in the browser for 15 minutes so revisiting the same origin/destination can render immediately. A fresh risk analysis still recomputes the score for its selected visit time, while reusing external data that remains within its TTL.
