"""RapidAPI Netflix Catalog data extractor."""

from typing import Any, Dict, List, Optional

import requests

from src.utils.config import settings
from src.utils.logger import logger


class NetflixExtractor:
    """Extracts recent catalog additions and details from RapidAPI Netflix endpoints."""

    def __init__(
        self, api_key: Optional[str] = None, host: Optional[str] = None
    ) -> None:
        self.api_key = api_key or settings.rapidapi_key
        self.host = host or settings.rapidapi_host
        self.base_url = f"https://{self.host}"

    @property
    def headers(self) -> Dict[str, str]:
        """Headers required for RapidAPI authentication."""
        return {
            "X-RapidAPI-Key": self.api_key or "",
            "X-RapidAPI-Host": self.host,
        }

    def fetch_recent_additions(
        self, days_back: int = 7, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch recently added titles on Netflix.

        Args:
            days_back: Number of days to look back for newly added titles.
            limit: Page size limit.
            offset: Pagination offset.

        Returns:
            List of raw title dictionaries.
        """
        if not self.api_key:
            logger.warning("No RAPIDAPI_KEY configured. Returning mock/stub response.")
            return self._get_mock_catalog_data()

        url = f"{self.base_url}/search"
        params = {
            "days": days_back,
            "limit": limit,
            "offset": offset,
            "order_by": "date",
        }

        try:
            logger.info(
                f"Extracting Netflix titles from {url} (days_back={days_back}, limit={limit})..."
            )
            response = requests.get(
                url, headers=self.headers, params=params, timeout=15
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results", [])
            logger.info(f"Successfully extracted {len(results)} Netflix titles.")
            return results
        except requests.RequestException as err:
            logger.error(f"Error fetching Netflix catalog data: {err}")
            return []

    def _get_mock_catalog_data(self) -> List[Dict[str, Any]]:
        """Mock fallback dataset for testing without an active API key."""
        return [
            {
                "id": "nf_812345",
                "title": "Stranger Things",
                "type": "series",
                "synopsis": "When a young boy vanishes, a small town uncovers a mystery...",
                "year": 2016,
                "runtime": 3000,
                "maturity_rating": "TV-14",
                "date_added": "2026-08-01",
            },
            {
                "id": "nf_898765",
                "title": "Glass Onion: A Knives Out Mystery",
                "type": "movie",
                "synopsis": "Tech billionaire Miles Bron invites his friends for a getaway...",
                "year": 2022,
                "runtime": 8340,
                "maturity_rating": "PG-13",
                "date_added": "2026-08-10",
            },
            {
                "id": "nf_554433",
                "title": "The Queen's Gambit",
                "type": "series",
                "synopsis": "Orphaned at the tender age of nine, prodigious introvert Beth Harmon...",
                "year": 2020,
                "runtime": 2400,
                "maturity_rating": "TV-MA",
                "date_added": "2026-08-15",
            },
        ]
