"""Main Orchestration Pipeline for StreamPulse: Live 2026 Catalog ELT & Real-Time Intelligence."""

import argparse
import sys
import time
from typing import Any, Dict, List, Optional
from src.extract.enricher_scraper import WebEnricher
from src.extract.historical_loader import HistoricalDatasetLoader
from src.extract.netflix import NetflixExtractor
from src.extract.netflix_scraper import NetflixWebScraper
from src.extract.tmdb import TMDbExtractor
from src.load.warehouse_loader import warehouse_loader
from src.transform.cleaner import clean_title_record
from src.transform.entity_resolution import EntityResolver
from src.transform.profiler import data_profiler
from src.utils.config import settings
from src.utils.db import db_manager
from src.utils.logger import logger


def run_pipeline_step(
    mode: str = "live",
    years: Optional[List[int]] = None,
    limit: int = 50,
    include_historical: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Execute a complete 5-step ELT pipeline cycle with validation and profiling.

    Args:
        mode: Pipeline mode ('live', 'full', 'stream', 'profile').
        years: List of release years to scrape (e.g. [2026, 2025]).
        limit: Limit on scraped items.
        include_historical: Whether to load 5,800+ historical baseline records.
        dry_run: If True, skips database writes.

    Returns:
        Dictionary summary of the pipeline execution.
    """
    if years is None:
        years = [2026, 2025]

    logger.info("================================================================================")
    logger.info(f"[PIPELINE] STREAMPULSE ELT RUN: [MODE={mode.upper()}]")
    logger.info(f"Target Years: {years} | Scrape Limit: {limit} | Historical: {include_historical}")
    logger.info("================================================================================")

    # -------------------------------------------------------------------------
    # STEP 1: Ingestion & Live 2026 Web Scraping
    # -------------------------------------------------------------------------
    logger.info("--- STEP 1/5: INGESTION & LIVE 2026 WEB SCRAPING ---")
    all_raw_titles: List[Dict[str, Any]] = []

    # 1.1 Historical Baseline (if requested)
    if include_historical or mode == "full":
        logger.info("Loading historical Kaggle enriched benchmark dataset...")
        hist_loader = HistoricalDatasetLoader()
        hist_records = hist_loader.load_historical_records(limit=settings.batch_size)
        logger.info(f"[OK] Ingested {len(hist_records):,} historical baseline titles.")
        all_raw_titles.extend(hist_records)

    # 1.2 RapidAPI Ingestion (if key configured)
    use_rapidapi = bool(
        settings.rapidapi_key and not settings.rapidapi_key.startswith("your_")
    )
    if use_rapidapi:
        logger.info("Extracting live catalog additions from RapidAPI Netflix...")
        netflix_extractor = NetflixExtractor()
        rapid_titles = netflix_extractor.fetch_recent_additions(days_back=14, limit=limit)
        logger.info(f"[OK] Ingested {len(rapid_titles)} titles from RapidAPI.")
        all_raw_titles.extend(rapid_titles)

    # 1.3 Zero-Cost Live Web Scraper (Wikipedia 2026 + RSS)
    logger.info("Scraping live 2026 Netflix originals, programming, and RSS feeds...")
    scraper = NetflixWebScraper()
    scraped_titles = scraper.scrape_live_catalog(
        years=years, include_series=True, include_feed=True, limit=limit
    )
    logger.info(f"[OK] Scraped {len(scraped_titles)} live 2025/2026 titles.")
    all_raw_titles.extend(scraped_titles)

    logger.info(f"Total raw titles collected for processing: {len(all_raw_titles):,}")

    # -------------------------------------------------------------------------
    # STEP 2: Cleaning & Normalization
    # -------------------------------------------------------------------------
    logger.info("--- STEP 2/5: DATA CLEANING & NORMALIZATION ---")
    cleaned_records: List[Dict[str, Any]] = []
    seen_ids = set()

    for raw in all_raw_titles:
        cleaned = clean_title_record(raw)
        nid = cleaned["netflix_id"]
        if nid not in seen_ids:
            seen_ids.add(nid)
            cleaned["source"] = raw.get("source", "scraped_live")
            if "director" in raw:
                cleaned["director"] = raw["director"]
            if "language" in raw:
                cleaned["language"] = raw["language"]
            if "genres" in raw:
                cleaned["genres"] = raw["genres"]
            elif "genre" in raw:
                cleaned["genre"] = raw["genre"]
            cleaned_records.append(cleaned)

    logger.info(f"[OK] Standardized and deduplicated {len(cleaned_records):,} title records.")

    # -------------------------------------------------------------------------
    # STEP 3: Entity Resolution & Audience Metrics Enrichment
    # -------------------------------------------------------------------------
    logger.info("--- STEP 3/5: ENTITY RESOLUTION & LIVE ENRICHMENT ---")
    tmdb_extractor = TMDbExtractor()
    resolver = EntityResolver(match_threshold=settings.fuzzy_match_threshold)
    web_enricher = WebEnricher()

    resolved_records: List[Dict[str, Any]] = []
    has_tmdb_key = bool(
        settings.tmdb_api_key and not settings.tmdb_api_key.startswith("your_")
    )

    for record in cleaned_records:
        title = record["title"]
        year = record["release_year"]
        media_type = record["media_type"]

        # If already enriched from Kaggle historical dataset
        if record.get("source") == "kaggle_historical_enriched" and record.get("tmdb_score"):
            enriched = {
                **record,
                "tmdb_id": record.get("imdb_id") or record.get("netflix_id"),
                "vote_average": record.get("tmdb_score", 0.0),
                "vote_count": record.get("imdb_votes", 0),
                "popularity": record.get("tmdb_popularity", 0.0),
                "match_confidence": 100.0,
            }
            resolved_records.append(enriched)
            continue

        # TMDb Resolution (if active API key)
        matched_candidate = None
        match_score = 0.0
        if has_tmdb_key:
            candidates = tmdb_extractor.search_title(title=title, year=year, media_type=media_type)
            matched_candidate, match_score = resolver.resolve(
                netflix_title=title, netflix_year=year, candidates=candidates
            )

        if matched_candidate:
            record["tmdb_id"] = matched_candidate.get("id")
            record["vote_average"] = matched_candidate.get("vote_average", 0.0)
            record["vote_count"] = matched_candidate.get("vote_count", 0)
            record["popularity"] = matched_candidate.get("popularity", 0.0)
            record["match_confidence"] = round(match_score, 2)

        # Zero-Cost Web Enrichment
        fully_enriched = web_enricher.enrich_title(record)
        resolved_records.append(fully_enriched)

    logger.info(f"[OK] Enriched and resolved {len(resolved_records):,} titles.")

    # -------------------------------------------------------------------------
    # STEP 4: Data Validation & Catalog Profiling
    # -------------------------------------------------------------------------
    logger.info("--- STEP 4/5: DATA QUALITY VALIDATION & PROFILING ---")
    profile_report = data_profiler.profile_dataset(resolved_records)

    # -------------------------------------------------------------------------
    # STEP 5: Warehouse Loading & Artifact Export
    # -------------------------------------------------------------------------
    logger.info("--- STEP 5/5: WAREHOUSE LOADING & MASTER EXPORT ---")
    load_summary = warehouse_loader.load_pipeline_records(resolved_records, dry_run=dry_run)

    # Print 2026 Sample Highlights
    sample_2026 = [r for r in resolved_records if (r.get("release_year") or 0) == 2026][:5]
    if sample_2026:
        logger.info("[HIGHLIGHTS] Live 2026 Catalog Highlights Preview:")
        for idx, item in enumerate(sample_2026, 1):
            logger.info(
                f"   {idx}. [{item.get('date_added', '2026')}] {item['title']} "
                f"({item.get('media_type', 'movie').upper()}) | "
                f"Rating: {item.get('vote_average')}/10 | Pop: {item.get('popularity')} | "
                f"Source: {item.get('source')}"
            )

    logger.info("================================================================================")
    logger.info("[SUCCESS] STREAMPULSE ELT PIPELINE COMPLETED SUCCESSFULLY")
    logger.info(
        f"Processed: {len(resolved_records):,} titles | "
        f"Quality: {profile_report.get('quality_score', 100)}% | "
        f"Parquet: {load_summary.get('exported_parquet')}"
    )
    logger.info("================================================================================")

    return {
        "records_count": len(resolved_records),
        "profile_report": profile_report,
        "load_summary": load_summary,
    }


def start_streaming_daemon(interval_seconds: int = 60, years: Optional[List[int]] = None) -> None:
    """Run real-time continuous streaming ingestion daemon."""
    logger.info("================================================================================")
    logger.info(f"[STREAM] STARTING REAL-TIME STREAMING DAEMON (Polling every {interval_seconds}s)")
    logger.info("Press Ctrl+C to terminate streaming daemon.")
    logger.info("================================================================================")

    cycle = 1
    try:
        while True:
            logger.info(f"\n[STREAM CYCLE #{cycle}] Polling live stream feeds at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            run_pipeline_step(
                mode="live",
                years=years or [2026],
                limit=30,
                include_historical=False,
                dry_run=False,
            )
            cycle += 1
            logger.info(f"Sleeping for {interval_seconds} seconds until next real-time poll...")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("[STREAM] Real-time streaming daemon stopped by user.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="StreamPulse: 2026 Live Netflix Catalog & Audience Intelligence ELT Pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["live", "full", "stream", "profile"],
        default="live",
        help="Pipeline execution mode: 'live' (2025/2026 releases), 'full' (historical + live), 'stream' (continuous), or 'profile' (profiling only)",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2026,2025",
        help="Comma-separated release years to scrape (e.g. '2026,2025' or '2026')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of titles to scrape per source",
    )
    parser.add_argument(
        "--stream-interval",
        type=int,
        default=60,
        help="Polling interval in seconds for streaming daemon mode",
    )
    parser.add_argument(
        "--include-historical",
        action="store_true",
        help="Include 5,800+ historical Kaggle benchmark records",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline in dry-run mode (skips database writes, exports files only)",
    )
    return parser.parse_args()


def main() -> None:
    """CLI Entry Point."""
    args = parse_args()
    parsed_years = [int(y.strip()) for y in args.years.split(",") if y.strip().isdigit()]

    if args.mode == "stream":
        start_streaming_daemon(interval_seconds=args.stream_interval, years=parsed_years)
    else:
        run_pipeline_step(
            mode=args.mode,
            years=parsed_years,
            limit=args.limit,
            include_historical=args.include_historical or (args.mode == "full"),
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception(f"Fatal error during StreamPulse execution: {exc}")
        sys.exit(1)
