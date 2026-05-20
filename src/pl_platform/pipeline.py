"""dlt pipeline for ingesting football-data.org into DuckDB.

Run with: python -m pl_platform.pipeline
"""

import logging
from pathlib import Path

import dlt

from pl_platform.api_client import FootballDataClient

logger = logging.getLogger(__name__)


@dlt.source(name="football_data")
def football_data_source(client: FootballDataClient):
    """One source per vendor; resources share auth + rate limiter via `client`."""

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

    return (competitions, teams)


def run_pipeline() -> None:
    """Execute the ingestion pipeline."""
    # Ensure data/ exists for the DuckDB file
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