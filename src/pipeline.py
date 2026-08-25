"""Main orchestration script for the StreamPulse ELT pipeline."""

import sys
from typing import Any, Dict, List
from src.extract.netflix import NetflixExtractor
from src.extract.netflix_scraper import NetflixWebScraper
from src.extract.tmdb import TMDbExtractor
from src.transform.cleaner import clean_title_record
from src.transform.entity_resolution import EntityResolver
from src.utils.config import settings
from src.utils.db import db_manager
from src.utils.logger import logger


def run_pipeline() -> None:
    """Execute the end-to-end extraction, resolution, and load process."""
    logger.info("=== Starting StreamPulse ELT Pipeline Run ===")

    # 1. Check Database Connectivity
    is_connected = db_manager.test_connection()
    if not is_connected:
        logger.warning("Database unavailable; proceeding in offline/dry-run simulation mode.")

    # 2. Extract from Netflix (API or Zero-Cost Web Scraper)
    if settings.rapidapi_key:
        logger.info("Using RapidAPI Netflix Extractor...")
        netflix_extractor = NetflixExtractor()
        raw_netflix_titles = netflix_extractor.fetch_recent_additions(days_back=14, limit=settings.batch_size)
    else:
        logger.info("No RAPIDAPI_KEY provided; executing zero-cost live Netflix Web Scraper...")
        scraper = NetflixWebScraper()
        raw_netflix_titles = scraper.scrape_live_catalog(limit=settings.batch_size)

    logger.info(f"Ingested {len(raw_netflix_titles)} Netflix catalog items.")

    # 3. Initialize TMDb & Entity Resolution
    tmdb_extractor = TMDbExtractor()
    resolver = EntityResolver(match_threshold=settings.fuzzy_match_threshold)

    resolved_records: List[Dict[str, Any]] = []
    unresolved_records: List[Dict[str, Any]] = []

    for raw in raw_netflix_titles:
        cleaned = clean_title_record(raw)
        title = cleaned["title"]
        year = cleaned["release_year"]
        media_type = cleaned["media_type"]

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

    # 4. Display sample preview of resolved items
    for item in resolved_records[:3]:
        logger.info(
            f"✓ [Match {item['match_confidence']}%] {item['title']} ({item['release_year']}) "
            f"| Rating: {item['vote_average']} | TMDb ID: {item['tmdb_id']}"
        )

    logger.info("=== StreamPulse Pipeline Run Completed Successfully ===")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        logger.exception(f"Fatal error during pipeline execution: {exc}")
        sys.exit(1)
