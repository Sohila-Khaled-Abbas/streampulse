"""Historical Netflix Dataset Loader and Enrichment Pipeline.

Fetches, parses, and enriches 5,800+ historical Netflix titles with IMDb & TMDb metrics
based on the Kaggle 'Netflix TV Shows and Movies enriched with IMDb & TMDb' dataset.
"""

import csv
import os
import urllib.request
from typing import Any, Dict, List, Optional

from src.utils.logger import logger

KAGGLE_MIRROR_URL = (
    "https://raw.githubusercontent.com/amirtds/kaggle-netflix-tv-shows-and-movies/main/titles.csv"
)
LOCAL_CACHE_PATH = os.path.join("data", "raw", "netflix_enriched_historical.csv")


class HistoricalDatasetLoader:
    """Ingests, caches, and transforms historical enriched Netflix catalog data."""

    def __init__(self, source_url: str = KAGGLE_MIRROR_URL, cache_path: str = LOCAL_CACHE_PATH) -> None:
        self.source_url = source_url
        self.cache_path = cache_path

    def download_dataset(self, force_refresh: bool = False) -> str:
        """Download and cache the historical dataset locally."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        if os.path.exists(self.cache_path) and not force_refresh:
            logger.info(f"Using cached historical dataset from {self.cache_path}")
            return self.cache_path

        logger.info(f"Downloading historical enriched dataset from {self.source_url}...")
        req = urllib.request.Request(self.source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")

        with open(self.cache_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Historical dataset saved to {self.cache_path}")
        return self.cache_path

    def load_historical_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load and parse historical records into standardized dictionary objects."""
        if not os.path.exists(self.cache_path):
            self.download_dataset()

        records: List[Dict[str, Any]] = []
        with open(self.cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                # Parse and clean metrics
                imdb_score = self._safe_float(row.get("imdb_score"))
                imdb_votes = self._safe_int(row.get("imdb_votes"))
                tmdb_score = self._safe_float(row.get("tmdb_score"))
                tmdb_pop = self._safe_float(row.get("tmdb_popularity"))
                runtime = self._safe_int(row.get("runtime"))
                release_year = self._safe_int(row.get("release_year"))

                # Standardize genre array string "['drama', 'crime']"
                raw_genres = row.get("genres", "[]")
                clean_genres = [
                    g.strip(" '\"[]") for g in raw_genres.split(",") if g.strip(" '\"[]")
                ]

                record = {
                    "netflix_id": row.get("id", f"hist_{idx}"),
                    "title": row.get("title", "").strip(),
                    "media_type": "series" if str(row.get("type", "")).upper() == "SHOW" else "movie",
                    "synopsis": row.get("description", ""),
                    "release_year": release_year,
                    "runtime_minutes": runtime,
                    "maturity_rating": row.get("age_certification") or "Unrated",
                    "genres": clean_genres,
                    "production_countries": row.get("production_countries", ""),
                    "seasons": self._safe_int(row.get("seasons")),
                    "imdb_id": row.get("imdb_id"),
                    "imdb_score": imdb_score,
                    "imdb_votes": imdb_votes,
                    "tmdb_score": tmdb_score,
                    "tmdb_popularity": tmdb_pop,
                    "date_added": f"{release_year or 2020}-01-01",
                    "source": "kaggle_historical_enriched",
                }
                records.append(record)

        logger.info(f"Loaded {len(records)} enriched historical titles from cache.")
        return records

    def validate_integrity(self) -> Dict[str, Any]:
        """Validate historical CSV file presence, row count, headers, and quality metrics."""
        if not os.path.exists(self.cache_path):
            self.download_dataset()

        file_size_bytes = os.path.getsize(self.cache_path)
        required_headers = [
            "id", "title", "type", "description", "release_year",
            "age_certification", "runtime", "genres", "imdb_id",
            "imdb_score", "imdb_votes", "tmdb_popularity", "tmdb_score"
        ]

        total_rows = 0
        min_year = 9999
        max_year = 0
        scored_imdb = 0
        scored_tmdb = 0

        with open(self.cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            missing_headers = [h for h in required_headers if h not in headers]

            for row in reader:
                total_rows += 1
                year = self._safe_int(row.get("release_year"))
                if year:
                    min_year = min(min_year, year)
                    max_year = max(max_year, year)
                if self._safe_float(row.get("imdb_score")) is not None:
                    scored_imdb += 1
                if self._safe_float(row.get("tmdb_score")) is not None:
                    scored_tmdb += 1

        validation = {
            "cache_path": self.cache_path,
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "total_records": total_rows,
            "min_release_year": min_year if min_year != 9999 else None,
            "max_release_year": max_year if max_year != 0 else None,
            "imdb_scored_titles": scored_imdb,
            "tmdb_scored_titles": scored_tmdb,
            "missing_headers": missing_headers,
            "is_valid": total_rows >= 5000 and len(missing_headers) == 0,
        }
        logger.info(
            f"Historical Dataset Integrity: {total_rows:,} records ({min_year}-{max_year}) | "
            f"IMDb Coverage: {scored_imdb:,} | Valid: {validation['is_valid']}"
        )
        return validation

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        try:
            return float(val) if val and str(val).strip() else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(val: Any) -> Optional[int]:
        try:
            return int(float(val)) if val and str(val).strip() else None
        except (ValueError, TypeError):
            return None

