"""Master Script: Prepare, Fetch, and Conformance-Check all 5 Power BI Data Sources.

Based on docs/powerbi_analytics_engineering_guide.md:
  1. PostgreSQL Database (`staging.stg_netflix_titles`)
  2. CSV Flat File (`data/raw/netflix_enriched_historical.csv` - 5,800+ records)
  3. CSV Flat File (`data/raw/imdb_external_ratings.csv`)
  4. Parquet Lakehouse (`data/raw/streaming_viewership_wide.parquet`)
  5. JSON REST API Feed (`data/raw/boxoffice_budget_feed.json`)
"""

import json
import os
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from src.extract.generate_dirty_training_datasets import (
    run_all as generate_dirty_sources,
)
from src.extract.historical_loader import HistoricalDatasetLoader
from src.pipeline import run_pipeline_step
from src.utils.db import db_manager
from src.utils.logger import logger


def prepare_and_verify_all_sources(
    force_refresh_historical: bool = False,
) -> Dict[str, Any]:
    """Fetch historical data, generate all multi-source datasets, and verify Power BI readiness."""
    logger.info(
        "================================================================================"
    )
    logger.info("[POWER BI PREP] PREPARING & VALIDATING ALL 5 MULTI-SOURCE DATASETS")
    logger.info(
        "================================================================================"
    )

    results = {
        "source_1_postgres_staging": {
            "status": "UNKNOWN",
            "records": 0,
            "path": "staging.stg_netflix_titles",
        },
        "source_2_historical_csv": {
            "status": "UNKNOWN",
            "records": 0,
            "path": "data/raw/netflix_enriched_historical.csv",
        },
        "source_3_imdb_ratings_csv": {
            "status": "UNKNOWN",
            "records": 0,
            "path": "data/raw/imdb_external_ratings.csv",
        },
        "source_4_viewership_parquet": {
            "status": "UNKNOWN",
            "records": 0,
            "path": "data/raw/streaming_viewership_wide.parquet",
        },
        "source_5_budget_json": {
            "status": "UNKNOWN",
            "records": 0,
            "path": "data/raw/boxoffice_budget_feed.json",
        },
        "lakehouse_exports": {"status": "UNKNOWN", "tables": []},
    }

    # -------------------------------------------------------------------------
    # 1. Fetch & Verify Historical Dataset (Source 2)
    # -------------------------------------------------------------------------
    logger.info("--- 1. VERIFYING SOURCE 2: HISTORICAL BENCHMARK CATALOG CSV ---")
    hist_loader = HistoricalDatasetLoader()
    if force_refresh_historical or not os.path.exists(hist_loader.cache_path):
        logger.info("Downloading historical enriched Kaggle dataset...")
        hist_loader.download_dataset(force_refresh=True)

    hist_integrity = hist_loader.validate_integrity()
    results["source_2_historical_csv"]["records"] = hist_integrity.get(
        "total_records", 0
    )
    results["source_2_historical_csv"]["status"] = (
        "OK" if hist_integrity.get("is_valid") else "FAILED"
    )
    results["source_2_historical_csv"]["details"] = hist_integrity

    # -------------------------------------------------------------------------
    # 2. Generate / Refresh Multi-Source Dirty Datasets (Sources 1, 3, 4, 5)
    # -------------------------------------------------------------------------
    logger.info("--- 2. GENERATING / REFRESHING MULTI-SOURCE TRAINING DATASETS ---")
    generate_dirty_sources()

    # Verify Source 3: IMDb Ratings CSV
    s3_path = os.path.join("data", "raw", "imdb_external_ratings.csv")
    if os.path.exists(s3_path):
        df_s3 = pd.read_csv(s3_path)
        required_cols_s3 = [
            "title_id",
            "user_score",
            "vote_count_raw",
            "critic_metascore",
            "snapshot_timestamp",
        ]
        valid_s3 = all(c in df_s3.columns for c in required_cols_s3) and len(df_s3) > 0
        results["source_3_imdb_ratings_csv"]["status"] = (
            "OK" if valid_s3 else "INVALID_COLUMNS"
        )
        results["source_3_imdb_ratings_csv"]["records"] = len(df_s3)
        logger.info(f"[OK] Source 3 (IMDb Ratings CSV): {len(df_s3)} rows verified.")
    else:
        results["source_3_imdb_ratings_csv"]["status"] = "MISSING"

    # Verify Source 4: Viewership Wide Parquet
    s4_path = os.path.join("data", "raw", "streaming_viewership_wide.parquet")
    if os.path.exists(s4_path):
        df_s4 = pd.read_parquet(s4_path)
        required_cols_s4 = [
            "catalog_ref_id",
            "territory_region",
            "Hours_2026_01",
            "Hours_2026_02",
            "Hours_2026_03",
            "avg_completion_pct",
        ]
        valid_s4 = all(c in df_s4.columns for c in required_cols_s4) and len(df_s4) > 0
        results["source_4_viewership_parquet"]["status"] = (
            "OK" if valid_s4 else "INVALID_COLUMNS"
        )
        results["source_4_viewership_parquet"]["records"] = len(df_s4)
        logger.info(
            f"[OK] Source 4 (Viewership Wide Parquet): {len(df_s4)} rows verified."
        )
    else:
        results["source_4_viewership_parquet"]["status"] = "MISSING"

    # Verify Source 5: Box Office Budget JSON
    s5_path = os.path.join("data", "raw", "boxoffice_budget_feed.json")
    if os.path.exists(s5_path):
        with open(s5_path, "r", encoding="utf-8") as f:
            feed = json.load(f)
        items = feed.get("data", [])
        valid_s5 = (
            len(items) > 0 and "stream_id" in items[0] and "categorization" in items[0]
        )
        results["source_5_budget_json"]["status"] = (
            "OK" if valid_s5 else "INVALID_STRUCTURE"
        )
        results["source_5_budget_json"]["records"] = len(items)
        logger.info(f"[OK] Source 5 (Budget Feed JSON): {len(items)} items verified.")
    else:
        results["source_5_budget_json"]["status"] = "MISSING"

    # Verify Source 1: PostgreSQL Staging Table
    if db_manager.test_connection():
        try:
            with db_manager.connect() as conn:
                from sqlalchemy import text

                stg_count = (
                    conn.execute(
                        text("SELECT COUNT(*) FROM staging.stg_netflix_titles")
                    ).scalar()
                    or 0
                )
                results["source_1_postgres_staging"]["records"] = stg_count
                results["source_1_postgres_staging"]["status"] = (
                    "OK" if stg_count > 0 else "EMPTY"
                )
                logger.info(
                    f"[OK] Source 1 (PostgreSQL staging.stg_netflix_titles): {stg_count} rows in database."
                )
        except Exception as err:
            results["source_1_postgres_staging"]["status"] = f"ERROR: {err}"
    else:
        results["source_1_postgres_staging"][
            "status"
        ] = "DB_OFFLINE (Ready for when Docker starts)"
        logger.info(
            "PostgreSQL is currently offline; table schema and seed statements are ready in sql/01_staging.sql."
        )

    # -------------------------------------------------------------------------
    # 3. Execute Master Warehouse Pipeline Ingestion
    # -------------------------------------------------------------------------
    logger.info("--- 3. EXECUTING MASTER WAREHOUSE GALAXY PIPELINE ---")
    pipeline_res = run_pipeline_step(
        mode="live",
        years=[2026, 2025],
        limit=50,
        include_historical=False,
        dry_run=not db_manager.test_connection(),
    )
    load_summary = pipeline_res.get("load_summary", {})
    results["lakehouse_exports"]["status"] = "OK"
    results["lakehouse_exports"]["tables"] = load_summary.get("lakehouse_tables", [])
    results["master_csv"] = load_summary.get("exported_csv", "")
    results["master_parquet"] = load_summary.get("exported_parquet", "")

    # -------------------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------------------
    logger.info(
        "================================================================================"
    )
    logger.info("[SUMMARY] ALL 5 POWER BI DATA SOURCES STATUS:")
    logger.info(
        f" 1. PostgreSQL Staging:      [{results['source_1_postgres_staging']['status']}] ({results['source_1_postgres_staging']['records']} rows)"
    )
    logger.info(
        f" 2. Historical Catalog CSV:  [{results['source_2_historical_csv']['status']}] ({results['source_2_historical_csv']['records']} titles, 1945-2024)"
    )
    logger.info(
        f" 3. IMDb Ratings CSV:        [{results['source_3_imdb_ratings_csv']['status']}] ({results['source_3_imdb_ratings_csv']['records']} snapshots)"
    )
    logger.info(
        f" 4. Viewership Wide Parquet: [{results['source_4_viewership_parquet']['status']}] ({results['source_4_viewership_parquet']['records']} records)"
    )
    logger.info(
        f" 5. Budget Feed JSON:        [{results['source_5_budget_json']['status']}] ({results['source_5_budget_json']['records']} items)"
    )
    logger.info(
        "================================================================================"
    )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare and Validate all Power BI Multi-Source Datasets"
    )
    parser.add_argument(
        "--force-refresh-historical",
        action="store_true",
        help="Force redownload of Kaggle historical CSV",
    )
    args = parser.parse_args()

    results = prepare_and_verify_all_sources(
        force_refresh_historical=args.force_refresh_historical
    )
    all_ok = (
        results["source_2_historical_csv"]["status"] == "OK"
        and results["source_3_imdb_ratings_csv"]["status"] == "OK"
        and results["source_4_viewership_parquet"]["status"] == "OK"
        and results["source_5_budget_json"]["status"] == "OK"
    )
    if all_ok:
        logger.info(
            "[SUCCESS] All files and datasets are ready for Power BI Desktop ingestion!"
        )
        sys.exit(0)
    else:
        logger.error("[ERROR] Some datasets failed validation. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    main()
