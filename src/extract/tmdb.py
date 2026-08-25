"""TMDb (The Movie Database) metadata and ratings extractor."""

from typing import Any, Dict, List, Optional
import requests
from src.utils.config import settings
from src.utils.logger import logger


class TMDbExtractor:
    """Queries TMDb API for canonical metadata, audience ratings, and popularity metrics."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.tmdb_api_key
        self.base_url = "https://api.themoviedb.org/3"

    def search_title(
        self, title: str, year: Optional[int] = None, media_type: str = "movie"
    ) -> List[Dict[str, Any]]:
        """Search TMDb for a title.

        Args:
            title: Title name.
            year: Optional release year.
            media_type: 'movie' or 'tv'.

        Returns:
            List of matching TMDb candidate records.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            logger.debug("No valid TMDB_API_KEY set; returning mock TMDb results.")
            return self._get_mock_tmdb_search(title, year)

        endpoint = "/search/tv" if media_type == "series" or media_type == "tv" else "/search/movie"
        url = f"{self.base_url}{endpoint}"
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": title,
            "include_adult": False,
        }
        if year:
            if endpoint == "/search/movie":
                params["year"] = year
            else:
                params["first_air_date_year"] = year

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.RequestException as err:
            logger.error(f"Error querying TMDb search for '{title}': {err}")
            return []

    def get_details(self, tmdb_id: int, media_type: str = "movie") -> Optional[Dict[str, Any]]:
        """Fetch full details and credit metrics for a given TMDb entity."""
        if not self.api_key:
            return None

        endpoint = f"/tv/{tmdb_id}" if media_type in ("series", "tv") else f"/movie/{tmdb_id}"
        url = f"{self.base_url}{endpoint}"
        params = {"api_key": self.api_key, "append_to_response": "credits,keywords"}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            logger.error(f"Error querying TMDb details for id={tmdb_id}: {err}")
            return None

    def _get_mock_tmdb_search(self, title: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Mock fallback TMDb data for local offline testing."""
        mock_db = {
            "stranger things": [
                {
                    "id": 66732,
                    "name": "Stranger Things",
                    "original_name": "Stranger Things",
                    "first_air_date": "2016-07-15",
                    "vote_average": 8.6,
                    "vote_count": 16500,
                    "popularity": 245.8,
                    "genre_ids": [18, 10765, 9648],
                }
            ],
            "glass onion: a knives out mystery": [
                {
                    "id": 661374,
                    "title": "Glass Onion: A Knives Out Mystery",
                    "original_title": "Glass Onion: A Knives Out Mystery",
                    "release_date": "2022-11-23",
                    "vote_average": 7.1,
                    "vote_count": 4800,
                    "popularity": 89.4,
                    "genre_ids": [35, 9648, 80],
                }
            ],
            "the queen's gambit": [
                {
                    "id": 87739,
                    "name": "The Queen's Gambit",
                    "original_name": "The Queen's Gambit",
                    "first_air_date": "2020-10-23",
                    "vote_average": 8.5,
                    "vote_count": 3900,
                    "popularity": 92.1,
                    "genre_ids": [18],
                }
            ],
        }
        clean = title.strip().lower()
        return mock_db.get(clean, [])
