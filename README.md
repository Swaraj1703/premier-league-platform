# Premier League Data Platform

End-to-end data engineering project: Premier League match data ingested from a real public REST API, transformed into a dimensional model, orchestrated with Dagster, and surfaced through a Next.js insights dashboard.

Built as a portfolio piece to demonstrate production data engineering patterns — auth, rate limits, incremental loads, dimensional modeling, asset-based orchestration — on a domain with real-world API constraints.

## Stack

| Layer | Tool |
| --- | --- |
| Source | [football-data.org](https://www.football-data.org/) REST API |
| Ingestion | [dlt](https://dlthub.com/) |
| Warehouse | [DuckDB](https://duckdb.org/) |
| Transformation | [dbt](https://www.getdbt.com/) + dbt-duckdb |
| Orchestration | [Dagster](https://dagster.io/) |
| Frontend | [Next.js](https://nextjs.org/) (Phase 5) |
| Packaging | hatchling |

## Architecture

Single DuckDB warehouse, three schemas:

- `raw_football` — dlt-managed, ingested 1:1 from the API
- `prep_football` — dbt views, 1:1 mirror with surrogate keys + type casting
- `prod_football` — dbt tables with business logic (standings, form, head-to-head)

The Phase 5 frontend reads static JSON/Parquet exports from `prod_football` — it never touches DuckDB directly.

## Setup

```bash
git clone https://github.com/Swaraj1703/premier-league-platform.git
cd premier-league-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env and add your football-data.org API key
```

Full setup including how to run the pipeline lands in Issue #8.

## Phase status

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | API client + dlt ingestion → `raw_football` | 🟡 In progress |
| 2 | dbt transformations: `prep_football` + `prod_football` | ⏳ Planned |
| 3 | Dagster orchestration (assets, schedules, exports) | ⏳ Planned |
| 4 | CI, contracts, Docker | ⏳ Planned |
| 5 | Next.js insights dashboard | ⏳ Planned |

## Project tracking

Issues, milestones, and progress are tracked via GitHub Issues and the Projects board. Each task = one issue = one PR.