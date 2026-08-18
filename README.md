# dev.ai

An AI-assisted test maintenance and reliability pipeline that runs automatically inside a project's own git workflow — scans code for untested functions, generates tests for them, independently verifies those tests are actually trustworthy before anything gets committed, and keeps a running changelog of what changed and why.

dev.ai lives inside this repository at [`ai-test-tool/`](ai-test-tool/). This repository, **Travel Planner**, is not the product — it's the sample application dev.ai was built and is run against, giving it a realistic codebase with real bugs, real tests, and a real AI feature to validate against during development. See [Running dev.ai against Travel Planner](#running-devai-against-travel-planner) below.

## Architecture

dev.ai is an orchestrator dispatching five agents across five stages — four fired automatically by git hooks or a file watcher, one (`init`) fired once, directly, by a person:

| Stage | Trigger | Agents that run |
|---|---|---|
| `pre-commit` | `git commit` | test-maintenance → reliability |
| `post-commit` | `git commit` | documentation |
| `pre-push` | `git push` | reliability (full-suite gate) |
| `on-save` | file save (via `watch`) | notification |
| `init` | `ai-test-tool init` (once) | test-maintenance (full-repo scan) → reliability |

**Agents:**
- **Orchestrator** (`orchestrator.py`) — maps a stage to its registered agents and dispatches them in order; isolates a crashing agent so it can't take down the whole hook chain.
- **Test-maintenance** (`agents/test_maintenance.py`) — finds functions with no test coverage and writes tests for them via Claude. Two scopes: `run()` scans only the current change (staged files, or the file just saved), capped at 5 functions per dispatch; `scan_repository()` (only on `init`) scans the entire repo, capped at 25. Function source is redacted for likely secrets (`secret_redaction.py`) before it's sent anywhere.
- **Reliability** (`agents/reliability.py`) — independently verifies whatever test-maintenance just generated: actually executes it, checks its assertions can fail, checks it isn't hallucinating code that doesn't exist, and checks it carries an AI-generated disclosure marker (EU AI Act, Article 50). This is what actually blocks a commit.
- **Documentation** (`agents/documentation.py`) — logs each commit's changes and reasoning to `CHANGELOG.md`.
- **Notification** (`agents/notification.py`) — reruns the test suite on every save and prints an immediate pass/fail, before anything is ever committed.

A human can always override a blocking result (`AI_TEST_TOOL_OVERRIDE=1`) — visibly, not silently: the override is printed and recorded, and shows up in the changelog entry it applies to. See [`ai-test-tool/RESPONSIBLE_AI.md`](ai-test-tool/RESPONSIBLE_AI.md) for the full accessibility, fairness, and data-handling commitments this is built on.

## Tech stack

- **Python 3.10+**, stdlib `ast` for static analysis (no heavier static-analysis dependency)
- **Claude API** (`anthropic`, optional extra) for test generation — the one genuine third-party network call in the pipeline, kept behind a single seam (`ai_client.py`) so the rest of the tool works without it
- **watchdog** for the file-save watcher
- **pytest** for dev.ai's own test suite (92 tests)
- **git hooks** (bash templates in `hooks/`) installed by `ai-test-tool init`, each with the absolute path to its own interpreter baked in at install time — not a fixed relative path, so the tool works regardless of where it's copied

## Running dev.ai against Travel Planner

From `ai-test-tool/`:

```bash
pip install -e ".[dev]"
```

For test generation, also install the AI extra and set an API key:

```bash
pip install -e ".[ai]"
```
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Install git hooks into Travel Planner (the parent directory) and run the initial full-repository scan:

```bash
python -m ai_test_tool.cli init ..
```

This installs `pre-commit`/`post-commit`/`pre-push`/`post-merge` hooks into Travel Planner's `.git/hooks/`, then scans the whole app for untested functions and generates tests for them (skip the scan with `--skip-scan`). Generated tests are written to disk, not auto-staged — review with `git diff`, then `git add` and commit whatever you're satisfied with.

Start live on-save notifications in a spare terminal:

```bash
python -m ai_test_tool.cli watch ..
```

Full setup, AI configuration, and extension details: [`ai-test-tool/README.md`](ai-test-tool/README.md).

---

## Travel Planner (the sample application)

A simple travel planner web app — register, create trips, and build a day-by-day itinerary with a live map, including an AI-generated itinerary planner backed by real OpenStreetMap data. Used as dev.ai's test subject, not developed as a product in its own right.

**Stack:** FastAPI (Python) · PostgreSQL · Redis · vanilla JS + Leaflet/OpenStreetMap frontend.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Running the app

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

### Running Travel Planner's own tests

Separate from dev.ai's own test suite — these test the pure business logic in `app/trip_logic.py`, which doesn't require the database or Redis:

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

### Project structure

```
ai-test-tool/     dev.ai — the actual tool this repository exists to test
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

### API overview

- `POST /auth/register` — create an account
- `POST /auth/login` — log in, returns a JWT
- `POST /auth/logout` — invalidate the current token
- `GET/POST /trips` — list or create trips
- `GET/DELETE /trips/{trip_id}` — view or delete a trip
- `GET/POST /trips/{trip_id}/itinerary` — list or add itinerary items

Interactive API docs are available at `/docs` once the app is running.

### Notes

- The map on the trip detail page uses OpenStreetMap tiles and the free Nominatim/Overpass APIs — fine for local development, but the public instances have rate limits and aren't meant for production traffic.
- Port `8080` (not `8000`) is used for the Docker-published app to avoid conflicts with other local services.
