"""Main orchestration script for the StreamPulse ELT pipeline."""

import sys
from typing import Any, Dict, List
from src.extract.historical_loader import HistoricalDatasetLoader
from src.extract.netflix import NetflixExtractor
from src.extract.netflix_scraper import NetflixWebScraper
from src.extract.tmdb import TMDbExtractor
from src.transform.cleaner import clean_title_record
from src.transform.entity_resolution import EntityResolver
from src.utils.config import settings
from src.utils.db import db_manager
from src.utils.logger import logger


def run_pipeline(include_historical: bool = True) -> None:
    """Execute the end-to-end extraction, resolution, and load process."""
    logger.info("=== Starting StreamPulse ELT Pipeline Run ===")

    # 1. Check Database Connectivity
    is_connected = db_manager.test_connection()
    if not is_connected:
        logger.warning("Database unavailable; proceeding in offline/dry-run simulation mode.")

    # 2. Ingest Historical Enriched Foundation (Kaggle Dataset)
    all_titles: List[Dict[str, Any]] = []
    if include_historical:
        logger.info("Loading historical enriched dataset (IMDb + TMDb)...")
        hist_loader = HistoricalDatasetLoader()
        historical_records = hist_loader.load_historical_records(limit=settings.batch_size)
        logger.info(f"Loaded {len(historical_records)} historical enriched titles.")
        all_titles.extend(historical_records)

    # 3. Extract Live Incremental Additions (API or Zero-Cost Web Scraper)
    use_rapidapi = bool(
        settings.rapidapi_key and not settings.rapidapi_key.startswith("your_")
    )
    if use_rapidapi:
        logger.info("Using RapidAPI Netflix Extractor for live deltas...")
        netflix_extractor = NetflixExtractor()
        live_titles = netflix_extractor.fetch_recent_additions(days_back=14, limit=25)
    else:
        logger.info("Executing zero-cost live Netflix Web Scraper for new releases...")
        scraper = NetflixWebScraper()
        live_titles = scraper.scrape_live_catalog(limit=25)

    logger.info(f"Ingested {len(live_titles)} live incremental catalog items.")
    all_titles.extend(live_titles)

    # 4. Initialize TMDb & Entity Resolution
    tmdb_extractor = TMDbExtractor()
    resolver = EntityResolver(match_threshold=settings.fuzzy_match_threshold)

    resolved_records: List[Dict[str, Any]] = []
    unresolved_records: List[Dict[str, Any]] = []

    for raw in all_titles:
        cleaned = clean_title_record(raw)
        title = cleaned["title"]
        year = cleaned["release_year"]
        media_type = cleaned["media_type"]

        # If already enriched from historical Kaggle dataset with TMDb/IMDb metrics
        if raw.get("source") == "kaggle_historical_enriched" and raw.get("tmdb_score"):
            record = {
                **cleaned,
                "tmdb_id": raw.get("imdb_id") or raw.get("netflix_id"),
                "vote_average": raw.get("tmdb_score", 0.0),
                "imdb_score": raw.get("imdb_score"),
                "vote_count": raw.get("imdb_votes", 0),
                "popularity": raw.get("tmdb_popularity", 0.0),
                "match_confidence": 100.0,
                "source": "kaggle_historical_enriched",
            }
            resolved_records.append(record)
            continue

        candidates = tmdb_extractor.search_title(title=title, year=year, media_type=media_type)
        best_match, score = resolver.resolve(netflix_title=title, netflix_year=year, candidates=candidates)

        if best_match:
            record = {
                **cleaned,
                "tmdb_id": best_match.get("id"),
                "vote_average": best_match.get("vote_average", 0.0),
                "vote_count": best_match.get("vote_count", 0),
                "popularity": best_match.get("popularity", 0.0),
                "match_confidence": round(score, 2),
            }
            resolved_records.append(record)
        else:
            unresolved_records.append({**cleaned, "match_confidence": round(score, 2)})

    logger.info(
        f"Pipeline Summary: {len(resolved_records)} titles resolved successfully, "
        f"{len(unresolved_records)} pending review."
    )

    # 5. Display sample preview of resolved items
    for item in resolved_records[:3]:
        logger.info(
            f"[OK] [Match {item['match_confidence']}%] {item['title']} ({item['release_year']}) "
            f"| Rating: {item['vote_average']} | TMDb/IMDb ID: {item['tmdb_id']}"
        )

    logger.info("=== StreamPulse Pipeline Run Completed Successfully ===")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        logger.exception(f"Fatal error during pipeline execution: {exc}")
        sys.exit(1)
