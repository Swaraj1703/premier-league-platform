"""HTTP client for football-data.org."""

import logging
import os
import time
from datetime import date

import httpx
from dotenv import load_dotenv

from pl_platform.rate_limiter import TokenBucket

load_dotenv()
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when the API returns an unrecoverable error or exhausts retries."""


class FootballDataClient:
    """Client for the football-data.org REST API.

    Handles rate limiting (10 req/min), authentication, and retry logic
    for transient errors (429, 5xx, network).

    Example:
        client = FootballDataClient()  # reads FOOTBALL_DATA_API_KEY from .env
        teams = client.get_teams()      # returns parsed JSON dict
    """

    BASE_URL = "https://api.football-data.org/v4"
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        if not self.api_key:
            raise APIError(
                "FOOTBALL_DATA_API_KEY not found. "
                "Set it in .env or pass api_key explicitly."
            )
        self.bucket = TokenBucket(capacity=10, refill_rate=10 / 60)
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-Auth-Token": self.api_key},
            timeout=self.TIMEOUT_SECONDS,
        )

    def _request(self, path: str, params: dict | None = None) -> dict:
        """Make a rate-limited HTTP request with retry on transient errors."""
        self.bucket.acquire()  # one rate-limit slot per logical call

        for attempt in range(self.MAX_RETRIES + 1):
            start = time.monotonic()

            try:
                response = self._client.get(path, params=params)
            except httpx.RequestError as e:
                # Network-level failure (timeout, connection refused, DNS, etc.)
                if attempt < self.MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning(
                        "Network error: %s, backing off %ds (retry %d/%d)",
                        e, wait, attempt + 1, self.MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                logger.error("Max retries exhausted for %s%s", self.BASE_URL, path)
                raise APIError(f"Network error after {self.MAX_RETRIES + 1} attempts: {e}") from e

            elapsed_ms = (time.monotonic() - start) * 1000
            logger.info(
                "GET %s%s -> %d in %.0fms",
                self.BASE_URL, path, response.status_code, elapsed_ms,
            )

            # Success
            if response.status_code == 200:
                return response.json()

            # 429: respect Retry-After header, fall back to exponential
            if response.status_code == 429:
                if attempt < self.MAX_RETRIES:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = max(int(retry_after), 1) if retry_after else 2 ** attempt
                    except (TypeError, ValueError):
                        # Retry-After could be HTTP-date format; fall back to exponential
                        wait = 2 ** attempt
                    logger.warning(
                        "429 received, sleeping %ds (retry %d/%d)",
                        wait, attempt + 1, self.MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                logger.error("Max retries exhausted for %s%s", self.BASE_URL, path)
                raise APIError(f"Rate limited after {self.MAX_RETRIES} retries")

            # 5xx: exponential backoff
            if 500 <= response.status_code < 600:
                if attempt < self.MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning(
                        "%d received, backing off %ds (retry %d/%d)",
                        response.status_code, wait, attempt + 1, self.MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                logger.error("Max retries exhausted for %s%s", self.BASE_URL, path)
                raise APIError(f"Server error {response.status_code} after {self.MAX_RETRIES} retries")

            # 4xx non-429: permanent failure, raise immediately
            logger.error(
                "Permanent error %d for %s%s: %s",
                response.status_code, self.BASE_URL, path, response.text,
            )
            raise APIError(f"API error {response.status_code}: {response.text}")

        # Defensive: should never reach here
        raise APIError("Unexpected: exited retry loop without returning or raising")

    def get_competition(self, competition: str = "PL") -> dict:
        """Get competition metadata."""
        return self._request(f"/competitions/{competition}")

    def get_teams(self, competition: str = "PL") -> dict:
        """Get all teams in a competition."""
        return self._request(f"/competitions/{competition}/teams")

    def get_matches(
        self,
        date_from: date,
        date_to: date,
        competition: str = "PL",
    ) -> dict:
        """Get matches in a competition within a date range."""
        return self._request(
            f"/competitions/{competition}/matches",
            params={
                "dateFrom": date_from.isoformat(),
                "dateTo": date_to.isoformat(),
            },
        )

    def get_scorers(self, season: int, competition: str = "PL") -> dict:
        """Get top scorers for a competition season."""
        return self._request(
            f"/competitions/{competition}/scorers",
            params={"season": season},
        )

    def close(self) -> None:
        """Close the underlying HTTP client and release its connection pool."""
        self._client.close()

    def __enter__(self) -> "FootballDataClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
