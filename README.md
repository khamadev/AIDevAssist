# Travel Planner

A simple travel planner web app — register, create trips, and build a day-by-day itinerary with a live map. Built as a skeleton application for testing AI-assisted unit test generation.

**Stack:** FastAPI (Python) · PostgreSQL · Redis · vanilla JS + Leaflet/OpenStreetMap frontend.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Running the app

From the project root:

```bash
docker compose up --build
```

This starts the app, PostgreSQL, and Redis together — no additional setup required. Once it's up, open:

```
http://127.0.0.1:8080/
```

To stop everything:

```bash
docker compose down
```

## Running tests

Tests run locally (outside Docker) against the pure business logic in `app/trip_logic.py`, which doesn't require the database or Redis:

```bash
python -m venv .venv
```

Windows (PowerShell):
```powershell
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pytest -q
```

macOS/Linux:
```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q
```

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
