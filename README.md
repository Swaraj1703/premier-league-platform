# Premier League Data Platform

![CI](https://github.com/Swaraj1703/premier-league-platform/actions/workflows/ci.yml/badge.svg)

End-to-end data platform ingesting Premier League data from [football-data.org](https://www.football-data.org/), modeling it with dbt, orchestrating with Dagster, and surfacing insights through a Next.js frontend. Designed as a portfolio project demonstrating modern data engineering practices end to end.

## Stack

| Layer | Tool |
|---|---|
| Ingestion | [dlt](https://dlthub.com/) |
| Warehouse | [DuckDB](https://duckdb.org/) |
| Transformation | [dbt](https://www.getdbt.com/) |
| Orchestration | [Dagster](https://dagster.io/) |
| HTTP client | [httpx](https://www.python-httpx.org/) |
| Frontend | [Next.js](https://nextjs.org/) |

## Architecture

The warehouse uses a three-schema layered design that lets each tool own one concern cleanly:

```
   football-data.org API
            |  HTTP (auth, rate limit, retry)
            v
   FootballDataClient                          (src/pl_platform/api_client.py)
            |  returns Python dicts
            v
   dlt source + resources                      (src/pl_platform/pipeline.py)
            |  yields dicts
            v
   dlt pipeline                                (schema infer, normalize, batch)
            |
            v
   DuckDB at data/warehouse.duckdb
     |-- raw_football      <-- dlt writes here    (current scope)
     |-- prep_football     <-- dbt views          (Phase 2)
     +-- prod_football     <-- dbt models         (Phase 2)
```

- **`raw_football`** — faithful mirror of API responses, normalized into parent + child tables by dlt
- **`prep_football`** — dbt views with consistent naming, surrogate keys, light cleaning (1:1 with raw)
- **`prod_football`** — dimensional model: `dim_teams`, `dim_seasons`, `fct_matches`, `fct_team_match_results`, `fct_player_season_scoring`

## Quickstart

```bash
# Clone and set up
git clone https://github.com/Swaraj1703/premier-league-platform.git
cd premier-league-platform

# Create virtualenv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure API key (register free at football-data.org/client/register)
cp .env.example .env
# then edit .env and set FOOTBALL_DATA_API_KEY=<your-token>

# Run the ingestion pipeline
python -m pl_platform.pipeline
```

After the first run, `data/warehouse.duckdb` contains four resource tables plus dlt's bookkeeping tables.

## Pipeline

The pipeline (`src/pl_platform/pipeline.py`) defines one dlt source (`football_data_source`) with four resources. Each resource calls a method on `FootballDataClient` and yields the response into a corresponding table under the `raw_football` schema.

| Resource | Endpoint | Disposition | Rows (typical) |
|---|---|---|---|
| `competitions` | `/competitions/PL` | `replace` | 1 |
| `teams` | `/competitions/PL/teams` | `replace` | 20 |
| `matches` | `/competitions/PL/matches?dateFrom=...&dateTo=...` | `merge` on `id` | varies by date range |
| `scorers` | `/competitions/PL/scorers?season=...` | `replace` | ~10 |

### Source parameters

`football_data_source` accepts three optional parameters with sensible defaults:

| Parameter | Default | Affects |
|---|---|---|
| `date_from` | 30 days before `date_to` | `matches` only |
| `date_to` | `date.today()` | `matches` only |
| `season` | current PL season (year if month >= August, else year - 1) | `scorers` only |

Defaults make `python -m pl_platform.pipeline` work with no arguments. Custom ranges or seasons can be passed by importing and calling `football_data_source` directly — useful for backfills or once Dagster takes over orchestration in Phase 3.

### Season boundary

`_current_pl_season()` resolves the PL season start year. PL seasons begin in August, so:

- January through July → `today.year - 1` (the season that started last August is still active)
- August through December → `today.year` (a new season has just started)

Edge case worth knowing: between August 1 and the first matchday (~mid-August), the helper advertises the new season while the API may still be returning the previous season's leaderboard. Not relevant for daily use; flagged here so future-you doesn't get confused if results look stale in early August.

### Merge semantics for matches

Of the four resources, only `matches` uses `merge` disposition (with `primary_key="id"`). Reason: match state evolves after first ingestion — SCHEDULED matches become FINISHED, scores fill in, attendance gets backfilled. Merge upserts on `id`, so re-running the pipeline with overlapping date ranges correctly updates existing rows without duplicating them.

Known limitation: merge only refreshes matches inside the current date window. Matches outside the window can become stale. Phase 3 (Dagster) will combine a wide initial backfill with a rolling 30-day window for incremental updates.

## Querying the warehouse

DuckDB has both a Python API and a standalone CLI. Either works.

### CLI

```bash
duckdb data/warehouse.duckdb
```

Then at the prompt:

```sql
SHOW ALL TABLES;
SELECT name, tla FROM raw_football.teams ORDER BY name;
SELECT player__name, team__name, goals
FROM raw_football.scorers
ORDER BY goals DESC LIMIT 5;
```

### Python REPL

```python
import duckdb
con = duckdb.connect('data/warehouse.duckdb', read_only=True)
con.sql("SELECT COUNT(*) FROM raw_football.matches").show()
con.sql("DESCRIBE raw_football.scorers").show()
```

## Testing

Unit tests live in `tests/` and run with pytest:

```bash
pytest tests/ -v
```

Current coverage:

- `test_rate_limiter.py` — token bucket behavior with injected fake clock
- `test_pipeline.py` — source structure (resource names, write dispositions) using a mocked `FootballDataClient`

CI runs the same `pytest tests/ -v` on every push to `main` and every PR via `.github/workflows/ci.yml`. Tests deliberately do not hit the live API; the smoke run is a local-only verification.

## Phase status

| Phase | Status |
|---|---|
| **Phase 1: Raw ingestion** (4 resources + CI + docs) | Complete |
| Phase 2: dbt transformations | Next |
| Phase 3: Dagster orchestration | Planned |
| Phase 4: Docker packaging + data contracts | Planned |
| Phase 5: Next.js insights frontend | Planned |

Issue tracker: [GitHub Issues](https://github.com/Swaraj1703/premier-league-platform/issues).