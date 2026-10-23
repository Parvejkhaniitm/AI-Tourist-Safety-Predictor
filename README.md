# SafeRoute AI

Vue 3 + Vite frontend for a destination risk analysis and route comparison demo. The frontend supports local mock mode and a Flask REST API backend.

## Frontend

```sh
npm install
npm run dev
```

The default `.env.example` configuration uses mock data. To use Flask, set `VITE_API_MODE=live` in the root `.env`; leave `VITE_API_BASE_URL` empty for the Vite proxy to `http://127.0.0.1:5000`.

## Backend

See [API_CONTRACT.md](./API_CONTRACT.md) for the end-to-end backend design, API schemas, data model, safety controls, and current integration limits. To start the Flask service:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
flask --app wsgi run --debug --port 5000
```

Local SQLite is the default. Configure `DATABASE_URL` for PostgreSQL and replace the development secrets before deployment. External weather, crowd, verified incident, directions, and trained ML providers require real data sources and credentials; the backend intentionally marks these as unavailable rather than fabricating safety information.
