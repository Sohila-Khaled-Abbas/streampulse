"""Historical Netflix Dataset Loader and Enrichment Pipeline.

Fetches, parses, and enriches 7,780+ historical Netflix titles with IMDb & TMDb metrics
based on the Kaggle 'zohairbaloch/netflix-titles-enriched-with-imdb-and-tmdb' dataset.
"""

import csv
import os
import shutil
import urllib.request
from typing import Any, Dict, List, Optional

from src.utils.logger import logger

KAGGLE_DATASET_ID = "zohairbaloch/netflix-titles-enriched-with-imdb-and-tmdb"
KAGGLE_MIRROR_URL = "https://raw.githubusercontent.com/amirtds/kaggle-netflix-tv-shows-and-movies/main/titles.csv"
LOCAL_CACHE_PATH = os.path.join("data", "raw", "netflix_enriched_historical.csv")


class HistoricalDatasetLoader:
    """Ingests, caches, and transforms historical enriched Netflix catalog data."""

    def __init__(
        self,
        dataset_id: str = KAGGLE_DATASET_ID,
        source_url: str = KAGGLE_MIRROR_URL,
        cache_path: str = LOCAL_CACHE_PATH,
    ) -> None:
        self.dataset_id = dataset_id
        self.source_url = source_url
        self.cache_path = cache_path

    def download_dataset(self, force_refresh: bool = False) -> str:
        """Download and cache the full historical dataset locally from Kaggle."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        if os.path.exists(self.cache_path) and not force_refresh:
            logger.info(f"Using cached historical dataset from {self.cache_path}")
            return self.cache_path

        # 1. Primary: Download via KaggleHub
        try:
            import kagglehub

            logger.info(
                f"Downloading full Kaggle dataset '{self.dataset_id}' via kagglehub..."
            )
            kaggle_dir = kagglehub.dataset_download(self.dataset_id)
            logger.info(f"KaggleHub cached to: {kaggle_dir}")

            csv_candidates = [
                os.path.join(kaggle_dir, "netflix_content_intelligence_combined.csv"),
                os.path.join(kaggle_dir, "titles.csv"),
                os.path.join(kaggle_dir, "netflix_titles_enriched.csv"),
            ]
            found_src = None
            for cand in csv_candidates:
                if os.path.exists(cand):
                    found_src = cand
                    break

            if not found_src:
                all_csvs = [
                    os.path.join(kaggle_dir, f)
                    for f in os.listdir(kaggle_dir)
                    if f.endswith(".csv")
                ]
                if all_csvs:
                    all_csvs.sort(key=lambda x: os.path.getsize(x), reverse=True)
                    found_src = all_csvs[0]

            if found_src:
                shutil.copy2(found_src, self.cache_path)
                logger.info(
                    f"[SUCCESS] Historical dataset cached to {self.cache_path} from {found_src}"
                )
                return self.cache_path
        except Exception as err:
            logger.warning(
                f"KaggleHub download failed or unavailable ({err}). Attempting mirror fallback..."
            )

        # 2. Fallback: Download from raw mirror URL
        try:
            logger.info(
                f"Downloading historical enriched dataset from mirror: {self.source_url}..."
            )
            req = urllib.request.Request(
                self.source_url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")

            with open(self.cache_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Historical dataset saved from mirror to {self.cache_path}")
            return self.cache_path
        except Exception as err:
            logger.error(f"Error downloading historical dataset: {err}")
            return self.cache_path

    def load_historical_records(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load and parse historical records into standardized dictionary objects."""
        if not os.path.exists(self.cache_path):
            self.download_dataset()

        records: List[Dict[str, Any]] = []
        with open(self.cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                # ID resolution (supports content_id or id)
                nid = row.get("content_id") or row.get("id") or f"hist_{idx}"

                # Metric resolution (supports both naming schemes)
                imdb_score = self._safe_float(
                    row.get("imdb_rating")
                ) or self._safe_float(row.get("imdb_score"))
                imdb_votes = self._safe_int(row.get("imdb_votes"))
                tmdb_score = self._safe_float(
                    row.get("tmdb_rating")
                ) or self._safe_float(row.get("tmdb_score"))
                tmdb_pop = self._safe_float(row.get("tmdb_popularity"))
                runtime = self._safe_int(row.get("runtime_minutes")) or self._safe_int(
                    row.get("runtime")
                )
                release_year = self._safe_int(row.get("release_year"))

                # Standardize genres (supports semicolon, comma, and list string representations)
                raw_genres = row.get("genres", "")
                if ";" in raw_genres:
                    clean_genres = [
                        g.strip() for g in raw_genres.split(";") if g.strip()
                    ]
                elif "[" in raw_genres:
                    clean_genres = [
                        g.strip(" '\"[]")
                        for g in raw_genres.split(",")
                        if g.strip(" '\"[]")
                    ]
                else:
                    clean_genres = [
                        g.strip() for g in raw_genres.split(",") if g.strip()
                    ]

                raw_type = str(row.get("type", "")).upper()
                media_type = (
                    "series" if "TV" in raw_type or "SHOW" in raw_type else "movie"
                )
                rating = row.get("rating") or row.get("age_certification") or "TV-MA"
                date_added = row.get("date_added") or f"{release_year or 2020}-01-01"

                record = {
                    "netflix_id": nid,
                    "title": row.get("title", "").strip(),
                    "media_type": media_type,
                    "synopsis": row.get("description", ""),
                    "release_year": release_year,
                    "runtime_minutes": runtime or 90,
                    "maturity_rating": rating,
                    "genres": clean_genres,
                    "production_countries": row.get("countries")
                    or row.get("production_countries", ""),
                    "directors": row.get("directors") or row.get("director", ""),
                    "cast": row.get("cast", ""),
                    "seasons": self._safe_int(row.get("seasons")),
                    "imdb_id": row.get("imdb_id"),
                    "imdb_score": imdb_score,
                    "imdb_votes": imdb_votes,
                    "tmdb_score": tmdb_score,
                    "tmdb_popularity": tmdb_pop,
                    "date_added": date_added,
                    "source": "kaggle_historical_enriched",
                }
                records.append(record)

        logger.info(f"Loaded {len(records):,} enriched historical titles from cache.")
        return records

    def validate_integrity(self) -> Dict[str, Any]:
        """Validate historical CSV file presence, row count, headers, and quality metrics."""
        if not os.path.exists(self.cache_path):
            self.download_dataset()

        file_size_bytes = os.path.getsize(self.cache_path)

        total_rows = 0
        min_year = 9999
        max_year = 0
        scored_imdb = 0
        scored_tmdb = 0

        with open(self.cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            has_id = "content_id" in headers or "id" in headers
            has_title = "title" in headers
            has_year = "release_year" in headers

            for row in reader:
                total_rows += 1
                year = self._safe_int(row.get("release_year"))
                if year:
                    min_year = min(min_year, year)
                    max_year = max(max_year, year)
                if (
                    self._safe_float(row.get("imdb_rating")) is not None
                    or self._safe_float(row.get("imdb_score")) is not None
                ):
                    scored_imdb += 1
                if (
                    self._safe_float(row.get("tmdb_rating")) is not None
                    or self._safe_float(row.get("tmdb_score")) is not None
                ):
                    scored_tmdb += 1

        is_valid = total_rows >= 5000 and has_id and has_title and has_year

        validation = {
            "cache_path": self.cache_path,
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "total_records": total_rows,
            "min_release_year": min_year if min_year != 9999 else None,
            "max_release_year": max_year if max_year != 0 else None,
            "imdb_scored_titles": scored_imdb,
            "tmdb_scored_titles": scored_tmdb,
            "headers_count": len(headers),
            "is_valid": is_valid,
        }
        logger.info(
            f"Historical Dataset Integrity: {total_rows:,} records ({min_year}-{max_year}) | "
            f"IMDb Coverage: {scored_imdb:,} | TMDb Coverage: {scored_tmdb:,} | Valid: {is_valid}"
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
