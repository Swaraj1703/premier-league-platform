"""dlt pipeline for ingesting football-data.org into DuckDB.

Run with: python -m pl_platform.pipeline
"""

import logging
from datetime import date, timedelta
from pathlib import Path

import dlt

from pl_platform.api_client import FootballDataClient

logger = logging.getLogger(__name__)


def _current_pl_season() -> int:
    """Return the start year of the current PL season (seasons begin in August)."""
    today = date.today()
    return today.year if today.month >= 8 else today.year - 1


@dlt.source(name="football_data")
def football_data_source(
    client: FootballDataClient,
    date_from: date | None = None,
    date_to: date | None = None,
    season: int | None = None,
):
    """One source per vendor; resources share auth + rate limiter via `client`.

    Defaults:
    - `date_from` / `date_to` → last 30 days, only affect `matches`
    - `season` → current PL season (Aug-Jul boundary), only affects `scorers`
    """

    effective_to = date_to or date.today()
    effective_from = date_from or (effective_to - timedelta(days=30))
    effective_season = _current_pl_season() if season is None else season

    @dlt.resource(name="competitions", write_disposition="replace")
    def competitions():
        """Fetch competition metadata for Premier League."""
        logger.info("Fetching competition metadata for PL")
        yield client.get_competition("PL")

    @dlt.resource(name="teams", write_disposition="replace")
    def teams():
        """Fetch all teams competing in Premier League."""
        logger.info("Fetching teams for PL")
        response = client.get_teams("PL")
        yield from response["teams"]

    @dlt.resource(name="matches", write_disposition="merge", primary_key="id")
    def matches():
        """Fetch matches in the configured date range (defaults to last 30 days).

        NOTE: Merge only refreshes matches inside the current window. Matches
        outside it can become stale. Phase 3 (Dagster) will combine a wide
        initial backfill with a rolling 30-day window for subsequent runs.
        """
        logger.info("Fetching matches from %s to %s for PL", effective_from, effective_to)
        response = client.get_matches(effective_from, effective_to, "PL")
        yield from response["matches"]

    @dlt.resource(name="scorers", write_disposition="replace")
    def scorers():
        """Fetch top scorers leaderboard for the configured PL season."""
        logger.info("Fetching top scorers for PL season %d", effective_season)
        response = client.get_scorers(effective_season, "PL")
        yield from response["scorers"]

    return (competitions, teams, matches, scorers)


def run_pipeline() -> None:
    """Execute the ingestion pipeline."""
    Path("data").mkdir(exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="pl_platform_ingest",
        destination=dlt.destinations.duckdb("data/warehouse.duckdb"),
        dataset_name="raw_football",
    )

    with FootballDataClient() as client:
        source = football_data_source(client)

        logger.info("Starting pipeline run")
        info = pipeline.run(source)
        logger.info("Pipeline run complete:\n%s", info)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    )
    run_pipeline()
