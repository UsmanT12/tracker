# WNBA Stats Tracker

A local-first WNBA performance explorer. An independent Selenium command imports
official WNBA box scores into PostgreSQL, FastAPI calculates season baselines and
game-by-game differences, and a Next.js interface visualizes each performance
above or below the player’s average.

## Architecture

```text
WNBA schedule and box scores
             |
             v
   Python scraper CLI
             |
             v
        PostgreSQL
             |
             v
       FastAPI JSON API
             |
             v
       Next.js frontend
```

The website never starts the scraper. Player identity comes from players found
in imported box scores; the application does not depend on a manually maintained
roster.

## Project structure

- `backend/` — FastAPI, SQLAlchemy models, Alembic migrations, statistics
  services, and the scraper CLI
- `frontend/` — Next.js performance explorer
- `scripts/` — one-time legacy database migration
- `legacy/original-python-project/` — preserved original scraper, CLI, and
  Matplotlib charts

## Configuration

Copy the example configuration and change the database password:

```bash
cp .env.example .env
```

The main settings are:

```dotenv
DATABASE_URL=postgresql+psycopg://wnba_user:change_me@localhost:5432/wnba_stats
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
SELENIUM_HEADLESS=true
```

Selenium Manager locates a compatible ChromeDriver automatically. Set
`CHROME_BINARY` only when Chrome is installed in a non-standard location.

## Start PostgreSQL

For a new local database:

```bash
docker compose up -d db
```

If PostgreSQL is already running locally, point `DATABASE_URL` at that database
instead.

## Install and migrate the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

### Import the old `player_stats` table

This is optional and leaves the old table unchanged. From the repository root,
with the backend environment active:

```bash
python scripts/migrate_legacy_player_stats.py
python scripts/migrate_legacy_player_stats.py --execute
```

The first command is a dry run. Review its row counts before using `--execute`.

## Run the web scraper

The scraper accepts any season and runs independently of the API and frontend:

```bash
cd backend
source .venv/bin/activate
python -m app.ingestion.cli scrape-season --season 2024
```

Useful development options:

```bash
python -m app.ingestion.cli scrape-season --season 2025 --headless
python -m app.ingestion.cli scrape-season --season 2026 --no-headless --completed-only
python -m app.ingestion.cli scrape-season --season 2024 --limit 5
python -m app.ingestion.cli scrape-season --season 2024 --force
python -m app.ingestion.cli scrape-season --season 2024 --stop-on-error
python -m app.ingestion.cli scrape-game --url "<box-score-url>"
```

The command records each run and game result, skips imported games by default,
and performs one atomic database transaction per game. Use `--completed-only`
for an active season: it switches the WNBA schedule to its complete history and
imports only cards marked `FINAL`, including overtime finals. Future, live,
postponed, and cancelled games are excluded before their pages are opened.

## Run the API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000/api/v1` and interactive
documentation is at `http://localhost:8000/docs`.

Core endpoints:

- `GET /api/v1/health`
- `GET /api/v1/data-status`
- `GET /api/v1/seasons`
- `GET /api/v1/players`
- `GET /api/v1/players/{player_id}/performance?season=2024&stat=pts`

## Run the frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Select a player, season, and statistic to compare
every valid game against the weighted or arithmetic season baseline.

## Tests and checks

```bash
cd backend
pytest
ruff check .

cd ../frontend
npm test
npm run lint
npm run typecheck
npm run build
```

## Calculation rules

- DNP rows remain visible but are excluded from averages and distributions.
- Counting statistics use the arithmetic mean across games played.
- Shooting percentages use total makes divided by total attempts.
- Games with zero attempts have no percentage value or comparison.
- Every colored result also includes a signed delta and text label.
- Turnovers retain their mathematical delta while using lower-is-better color
  semantics.

## Known limitations

- WNBA pages use generated markup that can change. Selectors are centralized in
  `backend/app/ingestion/selectors.py`; update the fallback list when parsing
  errors identify a changed selector.
- The WNBA web firewall may reject automated traffic from hosted or shared IP
  addresses. The CLI detects this response explicitly; retry from a local
  network or use `--no-headless`.
- Home/away, scores, starters, and stable source player IDs are stored when
  available, but older pages may not expose all of them.
- The legacy migration infers game identity from date and team names because the
  old table did not store source game IDs.
- The sportsbook provider is intentionally a placeholder. Historical players
  and statistics remain owned by the application database.
