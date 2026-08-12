# Travel Planner

A simple travel planner web app — register, create trips, and build a day-by-day itinerary with a live map. Built as a skeleton application for testing AI-assisted unit test generation.

**Stack:** FastAPI (Python) · PostgreSQL · Redis · vanilla JS + Leaflet/OpenStreetMap frontend.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended path), **or**
- Python 3.12+ if running locally without Docker

## Option 1: Run entirely in Docker (recommended)

From the project root:

```bash
docker compose up --build
```

This starts the app, PostgreSQL, and Redis together. Once it's up, open:

```
http://127.0.0.1:8080/
```

To stop everything:

```bash
docker compose down
```

## Option 2: Run the app locally, with only the databases in Docker

Useful if you want faster reload cycles while developing.

1. Start just Postgres and Redis:

   ```bash
   docker compose up -d db redis
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   ```

   Windows (PowerShell):
   ```powershell
   .venv\Scripts\pip install -r requirements.txt
   ```

   macOS/Linux:
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```

3. Create a `.env.local` file (points at `localhost` instead of Docker service names):

   ```
   DATABASE_URL=postgresql://travel:travel@localhost:5433/travel_planner
   REDIS_URL=redis://localhost:6380/0
   JWT_SECRET_KEY=change-me-to-a-long-random-value
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. Run the app, telling it to load `.env.local`:

   Windows (PowerShell):
   ```powershell
   $env:ENV_FILE = ".env.local"
   .venv\Scripts\uvicorn app.main:app --reload --port 8001
   ```

   macOS/Linux:
   ```bash
   ENV_FILE=.env.local .venv/bin/uvicorn app.main:app --reload --port 8001
   ```

5. Open `http://127.0.0.1:8001/`.

## Environment variables

Create a `.env` file (used by Docker) with the following, adjusting as needed:

```
DATABASE_URL=postgresql://travel:travel@db:5432/travel_planner
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=change-me-to-a-long-random-value
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string (used for JWT logout/blacklist) |
| `JWT_SECRET_KEY` | Secret used to sign auth tokens — change this for any real deployment |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long login tokens stay valid |

For local (non-Docker) runs, use a separate `.env.local` with `localhost`-based URLs instead of Docker service names — see `ENV_FILE` usage above.

## Running tests

```bash
.venv/bin/pytest -q      # macOS/Linux
.venv\Scripts\pytest -q  # Windows
```

Tests cover the pure business logic in `app/trip_logic.py` and don't require the database or Redis to be running.

## Project structure

```
app/
  core/          config, database, Redis, JWT/password security
  models/        SQLAlchemy models (User, Trip, ItineraryItem)
  routes/        API endpoints (auth, trips, itinerary)
  trip_logic.py  pure trip-related business logic (date math, overlap checks)
  schemas.py     Pydantic request/response models
  main.py        FastAPI app entrypoint
static/          frontend (login, dashboard, trip detail pages)
tests/           pytest suite
```

## API overview

- `POST /auth/register` — create an account
- `POST /auth/login` — log in, returns a JWT
- `POST /auth/logout` — invalidate the current token
- `GET/POST /trips` — list or create trips
- `GET/DELETE /trips/{trip_id}` — view or delete a trip
- `GET/POST /trips/{trip_id}/itinerary` — list or add itinerary items

Interactive API docs are available at `/docs` once the app is running.

## Notes

- The map on the trip detail page uses OpenStreetMap tiles and the free Nominatim geocoding API — fine for local development, but Nominatim's public API has a strict rate limit (1 request/second) and isn't meant for production traffic.
- Port `8080` (not `8000`) is used for the Docker-published app to avoid conflicts with other local services.
