"""Whoop API client for fetching health data."""

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from whoop_scraper.auth import WhoopAuth

logger = logging.getLogger(__name__)

BASE_URL = "https://api.prod.whoop.com/developer/v1"


def get_date_range(days: int) -> tuple[str, str]:
    """Get date range for API queries.

    Args:
        days: Number of days to go back

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


class WhoopAPIClient:
    """Client for Whoop API v1."""

    def __init__(self, auth: WhoopAuth) -> None:
        """Initialize API client.

        Args:
            auth: WhoopAuth instance for token management
        """
        self.auth = auth

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with valid access token."""
        token = self.auth.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make authenticated GET request.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response data
        """
        url = f"{BASE_URL}{endpoint}"
        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def _get_paginated(
        self,
        endpoint: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of all records from all pages
        """
        all_records: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "start": f"{start_date}T00:00:00.000Z",
                "end": f"{end_date}T23:59:59.999Z",
            }
            if next_token:
                params["nextToken"] = next_token

            data = self._get(endpoint, params)
            records = data.get("records", [])
            all_records.extend(records)

            next_token = data.get("next_token")
            if not next_token:
                break

        return all_records

    # User endpoints
    def get_user_profile(self) -> dict[str, Any]:
        """Get user profile information."""
        logger.info("Fetching user profile")
        data = self._get("/user/profile/basic")
        logger.info("Successfully fetched user profile")
        return data

    def get_body_measurement(self) -> dict[str, Any]:
        """Get user body measurement data."""
        logger.info("Fetching body measurement")
        data = self._get("/user/measurement/body")
        logger.info("Successfully fetched body measurement")
        return data

    # Cycle endpoints
    def get_cycles(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get physiological cycles.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of cycle records
        """
        logger.info("Fetching cycles from %s to %s", start_date, end_date)
        records = self._get_paginated("/cycle", start_date, end_date)
        logger.info("Successfully fetched %d cycle records", len(records))
        return records

    # Recovery endpoints
    def get_recovery(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get recovery data.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of recovery records
        """
        logger.info("Fetching recovery from %s to %s", start_date, end_date)
        records = self._get_paginated("/recovery", start_date, end_date)
        logger.info("Successfully fetched %d recovery records", len(records))
        return records

    # Sleep endpoints
    def get_sleep(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get sleep data.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of sleep records
        """
        logger.info("Fetching sleep from %s to %s", start_date, end_date)
        records = self._get_paginated("/activity/sleep", start_date, end_date)
        logger.info("Successfully fetched %d sleep records", len(records))
        return records

    # Workout endpoints
    def get_workouts(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get workout data.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of workout records
        """
        logger.info("Fetching workouts from %s to %s", start_date, end_date)
        records = self._get_paginated("/activity/workout", start_date, end_date)
        logger.info("Successfully fetched %d workout records", len(records))
        return records
