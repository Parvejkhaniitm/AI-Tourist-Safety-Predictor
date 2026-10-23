# SafeRoute API and backend design

This contract maps the current Vue site to Flask REST APIs. Base path is `/api`; all JSON errors use `{ "error": { "code": "...", "message": "..." } }`. Scores are **risk scores**: lower means lower estimated risk. A score is not a guarantee of personal safety.

## Website flows

| UI flow | Endpoint | Authentication | Purpose |
|---|---|---|---|
| Home suggestions | `GET /destinations?q=` | No | Return up to 20 active destination names |
| Destination analysis | `POST /analyze` | Optional bearer JWT | Gather available factors, score, persist analysis |
| Route comparison | `GET /routes?destination=&start=` | No | Compare shortest and lower-risk routes |
| Create account | `POST /auth/register` | No | Create user and issue access/refresh tokens |
| Sign in | `POST /auth/login` | No | Verify credentials and issue tokens |
| Refresh session | `POST /auth/refresh` | Refresh bearer | Issue short-lived access token |
| Sign out | `POST /auth/logout` | Bearer | Revoke presented token |
| Analysis history | `GET /history` | Access bearer | Return caller's latest 50 saved analyses |
| Service health | `GET /health` | No | Liveness check |

## Response contracts

`GET /api/destinations` returns `string[]`, matching the current Vue adapter.

`POST /api/analyze` accepts `{ "destination": "India Gate" }`. Success returns `{ destination, location, score, confidence, analyzedAt, factors, reasons, analysisId, modelVersion }`. Each factor has `key`, `title`, `text`, `impact` (`lowers | neutral | raises`), `impactLabel`, `dataLabel`, and `available`. Unknown provider data must have `available: false` and is excluded from scoring. `analyzedAt` is an ISO 8601 timestamp.

`GET /api/routes` accepts destination and an optional origin. Success shape expected by the UI is `{ destination, start, destinationLabel, shortest, safer }`; each route has `distanceKm`, `durationMin`, `score`, and `note`, while `safer` may be `null`. Until a real directions provider and street-level safety features are configured, the backend returns HTTP 503 with a stable error body rather than generating fake routes. The route page can continue to use mock mode for its illustrative demo.

Auth requests use `{ "email": "...", "password": "..." }`. Register/login return `{ accessToken, refreshToken, user: { id, email } }`. Send access token as `Authorization: Bearer <token>`. Use refresh tokens only at `/auth/refresh`.

## Service boundaries

The Flask app is organized as a modular monolith with replaceable provider adapters. Keep request parsing/validation in routes, persistence in SQLAlchemy models, provider calls in `providers.py`, and model inference/calibration in `scoring.py`. If load warrants it, the provider and inference modules can become separate services without changing the public API.

1. **API layer:** Flask, versioned URL prefix, CORS allowlist, JWT, validation, consistent errors, request IDs/rate limits at deployment gateway.
2. **Persistence:** PostgreSQL in production; SQLite locally. `User`, `Destination`, `Analysis`, `Incident`, and `RevokedToken` entities. Use Flask-Migrate for schema changes.
3. **Data adapters:** weather, geocoding/directions, crowd estimates, and curated historical incident aggregation. Each adapter reports source, observed-at time, freshness, and failure. Cache provider data with explicit TTL and never treat stale data as live.
4. **Scoring:** versioned pipeline; planned Random Forest/XGBoost can consume feature vectors only after a documented, representative, privacy-reviewed training set and offline calibration exist. Persist model version, feature availability, confidence, and score for auditability. The included `baseline-v1` is a neutral placeholder, not a trained safety model.
5. **Frontend:** `src/services/api.js` owns live/mock mode and response adapters. Views now call this service rather than importing mock modules directly. Keep local mock data clearly labeled and do not represent it as verified.

## Data model and safeguards

- `Destination` stores normalized display name and coordinates; add a PostGIS point if radius-based searches are required.
- `Incident` stores category, severity, event date, source, and verification state. Store aggregated/location-bucketed data; do not ingest victim names or precise personal data.
- `Analysis` stores score, confidence, factor snapshot, timestamp, destination, and model version so historical results do not change when providers update.
- `User` stores email and a Werkzeug password hash, never a plaintext password. Analysis history is scoped by user ID.
- `RevokedToken` supports logout. Production should use HTTPS, strong independently generated secrets, short access-token lifetime, rate limits on auth and analysis, password reset/email verification, security headers, and a shared revocation store if multiple API workers run.
- Treat provider outages as missing factors, lower confidence, and explain omissions. Do not silently fill data or return a confident numeric result from missing evidence.
- Scores are estimates, never emergency guidance or a promise of safe travel. Provide reporting/feedback and incident-data correction workflows before public launch.

## Local setup

From `backend/`, create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, then run `flask --app wsgi run --debug --port 5000`. The Vite dev proxy already forwards `/api` to port 5000. Set root `.env` values `VITE_API_MODE=live` and `VITE_API_BASE_URL=` to switch the frontend to Flask. `DEMO_DATA=true` seeds only the five currently supported Delhi destinations; disable it when using a managed database. Use migrations (`flask --app wsgi db init`, then `db migrate` and `db upgrade`) before production schema changes.

## Current implementation limits

Auth, data models, destination lookup, analysis persistence, history, and API wiring are scaffolded. Weather, crowd, incident, directions, and trained ML integrations are intentionally provider seams because the project has no credentials, licensed data source, verified training set, or deployment policy configured. The backend returns unavailable/missing signals instead of inventing those facts. Before launch, supply providers, calibrate scores with domain review, run migrations, and configure production secrets/database/rate limits.
