"""Main scraper orchestration for all Whoop API endpoints."""

import logging
from typing import Any

import psycopg

from whoop_scraper.api_client import WhoopAPIClient, get_date_range
from whoop_scraper.auth import DatabaseTokenStorage, WhoopAuth
from whoop_scraper.config import get_settings
from whoop_scraper.db import operations as ops

logger = logging.getLogger(__name__)


class WhoopScraper:
    """Orchestrates scraping all Whoop API endpoints and storing in database."""

    def __init__(
        self,
        days: int = 7,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        """Initialize scraper.

        Args:
            days: Number of days to scrape (default 7, ignored if start/end provided)
            start_date: Explicit start date (YYYY-MM-DD)
            end_date: Explicit end date (YYYY-MM-DD)
        """
        self.days = days
        if start_date and end_date:
            self.start_date = start_date
            self.end_date = end_date
        else:
            self.start_date, self.end_date = get_date_range(days)
        self.settings = get_settings()

        # Use database token storage for stateless container deployments
        # Encryption key is optional - if not set, tokens are stored in plaintext
        token_storage = DatabaseTokenStorage(
            self.settings.database_url,
            encryption_key=self.settings.encryption_key or None,
        )
        self.auth = WhoopAuth(token_storage=token_storage)
        self.client = WhoopAPIClient(self.auth)
        self.stats: dict[str, Any] = {}

    def scrape_all(self) -> dict[str, Any]:
        """Scrape all endpoints and store in database.

        Returns:
            Dictionary with statistics about what was scraped
        """
        logger.info(
            "Starting scrape for %d days: %s to %s",
            self.days, self.start_date, self.end_date
        )

        with psycopg.connect(self.settings.database_url) as conn:
            # User info (no date range)
            self._scrape_user_profile(conn)
            self._scrape_body_measurement(conn)

            # Time-series endpoints (with date range)
            self._scrape_cycles(conn)
            self._scrape_recovery(conn)
            self._scrape_sleep(conn)
            self._scrape_workouts(conn)

        logger.info("Scrape completed successfully")
        return self.stats

    def _scrape_user_profile(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape user profile endpoint."""
        try:
            logger.info("Scraping user_profile...")
            data = self.client.get_user_profile()
            ops.upsert_user_profile(conn, data)
            self.stats["user_profile"] = {"success": True, "records": 1}
        except Exception as e:
            logger.error("Failed to scrape user_profile: %s", e)
            self.stats["user_profile"] = {"success": False, "error": str(e)}

    def _scrape_body_measurement(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape body measurement endpoint."""
        try:
            logger.info("Scraping body_measurement...")
            data = self.client.get_body_measurement()
            ops.upsert_body_measurement(conn, data)
            self.stats["body_measurement"] = {"success": True, "records": 1}
        except Exception as e:
            logger.error("Failed to scrape body_measurement: %s", e)
            self.stats["body_measurement"] = {"success": False, "error": str(e)}

    def _scrape_cycles(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape physiological cycles endpoint."""
        try:
            logger.info("Scraping cycles...")
            data = self.client.get_cycles(self.start_date, self.end_date)
            count = ops.upsert_cycles(conn, data)
            self.stats["cycles"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape cycles: %s", e)
            self.stats["cycles"] = {"success": False, "error": str(e)}

    def _scrape_recovery(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape recovery endpoint."""
        try:
            logger.info("Scraping recovery...")
            data = self.client.get_recovery(self.start_date, self.end_date)
            count = ops.upsert_recovery(conn, data)
            self.stats["recovery"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape recovery: %s", e)
            self.stats["recovery"] = {"success": False, "error": str(e)}

    def _scrape_sleep(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape sleep endpoint."""
        try:
            logger.info("Scraping sleep...")
            data = self.client.get_sleep(self.start_date, self.end_date)
            count = ops.upsert_sleep(conn, data)
            self.stats["sleep"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape sleep: %s", e)
            self.stats["sleep"] = {"success": False, "error": str(e)}

    def _scrape_workouts(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape workouts endpoint."""
        try:
            logger.info("Scraping workouts...")
            data = self.client.get_workouts(self.start_date, self.end_date)
            count = ops.upsert_workouts(conn, data)
            self.stats["workouts"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape workouts: %s", e)
            self.stats["workouts"] = {"success": False, "error": str(e)}
