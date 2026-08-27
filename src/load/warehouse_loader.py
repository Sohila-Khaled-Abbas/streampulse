"""PostgreSQL Data Warehouse Loader for Staging and Reporting Star Schemas."""

import csv
import json
import os
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from src.utils.db import db_manager
from src.utils.logger import logger


class WarehouseLoader:
    """Loads transformed streaming records into PostgreSQL staging & Kimball dimensional model.

    Features:
    - Idempotent upserts for `staging.stg_netflix_titles` and `reporting.dim_titles`
    - Genre normalization and bridge table association
    - Snapshot logging into `reporting.fact_catalog_ratings`
    - Seamless local export to CSV & JSON for Power BI or offline validation
    """

    def __init__(self, output_dir: str = os.path.join("data", "processed")) -> None:
        self.output_dir = output_dir

    def load_pipeline_records(
        self, records: List[Dict[str, Any]], dry_run: bool = False
    ) -> Dict[str, Any]:
        """Load resolved and enriched catalog records into database and export files.

        Args:
            records: Enriched title records.
            dry_run: If True, skips database writes and performs export only.

        Returns:
            Dictionary summary of load statistics.
        """
        summary = {
            "total_records": len(records),
            "db_connected": False,
            "staging_inserted": 0,
            "dim_titles_upserted": 0,
            "facts_recorded": 0,
            "exported_csv": "",
            "exported_json": "",
        }

        # 1. Always export master file artifacts
        exported_csv, exported_json = self.export_to_files(records)
        summary["exported_csv"] = exported_csv
        summary["exported_json"] = exported_json

        # 2. Database Ingestion if connected and not dry_run
        if not dry_run and db_manager.test_connection():
            summary["db_connected"] = True
            logger.info("Connected to PostgreSQL warehouse. Starting transactional load...")
            try:
                with db_manager.connect() as conn:
                    # Ingest Staging
                    stg_count = self._load_staging(conn, records)
                    summary["staging_inserted"] = stg_count

                    # Ingest Dimensional & Fact Star Schema
                    dim_count, fact_count = self._load_dimensional_star_schema(conn, records)
                    summary["dim_titles_upserted"] = dim_count
                    summary["facts_recorded"] = fact_count

                logger.info(
                    f"Warehouse Load Complete: {summary['staging_inserted']} staging rows, "
                    f"{summary['dim_titles_upserted']} dimension rows, {summary['facts_recorded']} fact rows."
                )
            except Exception as err:
                logger.error(f"Error during warehouse load: {err}")
        else:
            logger.info(
                f"Operating in offline/file export mode. Master artifacts available at: {exported_csv}"
            )

        return summary

    def _load_staging(self, conn: Any, records: List[Dict[str, Any]]) -> int:
        """Insert raw records into staging.stg_netflix_titles."""
        stmt = text("""
            INSERT INTO staging.stg_netflix_titles (
                netflix_id, title, title_type, synopsis, release_year,
                date_added, runtime_seconds, maturity_rating, raw_json
            ) VALUES (
                :netflix_id, :title, :media_type, :synopsis, :release_year,
                CAST(:date_added AS timestamp), :runtime_seconds, :maturity_rating, CAST(:raw_json AS jsonb)
            )
            ON CONFLICT (netflix_id) DO UPDATE SET
                title = EXCLUDED.title,
                synopsis = EXCLUDED.synopsis,
                runtime_seconds = EXCLUDED.runtime_seconds,
                extracted_at = NOW();
        """)

        inserted = 0
        for r in records:
            runtime_mins = r.get("runtime_minutes") or 0
            date_added = r.get("date_added") or "2026-01-01"
            if len(date_added) == 10:
                date_added += " 00:00:00"

            params = {
                "netflix_id": str(r.get("netflix_id")),
                "title": str(r.get("title", ""))[:490],
                "media_type": str(r.get("media_type", "movie")),
                "synopsis": str(r.get("synopsis", "")),
                "release_year": r.get("release_year") or 2026,
                "date_added": date_added,
                "runtime_seconds": int(runtime_mins * 60),
                "maturity_rating": str(r.get("maturity_rating", "PG-13")),
                "raw_json": json.dumps(r, default=str),
            }
            conn.execute(stmt, params)
            inserted += 1

        return inserted

    def _load_dimensional_star_schema(
        self, conn: Any, records: List[Dict[str, Any]]
    ) -> tuple[int, int]:
        """Upsert records into reporting.dim_titles, reporting.dim_genres, and reporting.fact_catalog_ratings."""
        dim_stmt = text("""
            INSERT INTO reporting.dim_titles (
                netflix_id, tmdb_id, canonical_title, media_type, release_year,
                release_date, netflix_date_added, maturity_rating, runtime_minutes,
                match_confidence, is_active, updated_at
            ) VALUES (
                :netflix_id, :tmdb_id, :title, :media_type, :release_year,
                CAST(:release_date AS date), CAST(:netflix_date_added AS date), :maturity_rating,
                :runtime_minutes, :match_confidence, TRUE, NOW()
            )
            ON CONFLICT (netflix_id) DO UPDATE SET
                canonical_title = EXCLUDED.canonical_title,
                tmdb_id = COALESCE(EXCLUDED.tmdb_id, reporting.dim_titles.tmdb_id),
                maturity_rating = EXCLUDED.maturity_rating,
                runtime_minutes = EXCLUDED.runtime_minutes,
                match_confidence = EXCLUDED.match_confidence,
                updated_at = NOW()
            RETURNING title_key;
        """)

        fact_stmt = text("""
            INSERT INTO reporting.fact_catalog_ratings (
                title_key, snapshot_date, vote_average, vote_count,
                popularity_score, days_to_streaming, is_trending
            ) VALUES (
                :title_key, CURRENT_DATE, :vote_average, :vote_count,
                :popularity_score, :days_to_streaming, :is_trending
            );
        """)

        dim_count = 0
        fact_count = 0

        for r in records:
            netflix_id = str(r.get("netflix_id"))
            raw_tmdb = r.get("tmdb_id")
            try:
                tmdb_id = int(raw_tmdb) if raw_tmdb and str(raw_tmdb).isdigit() else None
            except Exception:
                tmdb_id = None

            date_str = str(r.get("date_added", "2026-01-01"))[:10]
            rel_year = r.get("release_year") or 2026

            dim_params = {
                "netflix_id": netflix_id,
                "tmdb_id": tmdb_id,
                "title": str(r.get("title", ""))[:490],
                "media_type": str(r.get("media_type", "movie")),
                "release_year": rel_year,
                "release_date": f"{rel_year}-01-01",
                "netflix_date_added": date_str,
                "maturity_rating": str(r.get("maturity_rating", "PG-13")),
                "runtime_minutes": r.get("runtime_minutes") or 90,
                "match_confidence": float(r.get("match_confidence", 100.0)),
            }

            res = conn.execute(dim_stmt, dim_params)
            row = res.fetchone()
            if row:
                title_key = row[0]
                dim_count += 1

                # Fact rating snapshot
                fact_params = {
                    "title_key": title_key,
                    "vote_average": float(r.get("vote_average", 0.0) or 0.0),
                    "vote_count": int(r.get("vote_count", 0) or 0),
                    "popularity_score": float(r.get("popularity", 0.0) or 0.0),
                    "days_to_streaming": int(r.get("days_to_streaming", 30) or 30),
                    "is_trending": bool(r.get("is_trending", False)),
                }
                conn.execute(fact_stmt, fact_params)
                fact_count += 1

        return dim_count, fact_count

    def export_to_files(self, records: List[Dict[str, Any]]) -> tuple[str, str]:
        """Export master datasets to CSV and JSON."""
        os.makedirs(self.output_dir, exist_ok=True)
        csv_file = os.path.join(self.output_dir, "netflix_catalog_enriched_master.csv")
        json_file = os.path.join(self.output_dir, "live_2026_pulse.json")

        if records:
            fieldnames = [
                "netflix_id", "title", "media_type", "release_year", "runtime_minutes",
                "maturity_rating", "synopsis", "vote_average", "vote_count", "popularity",
                "imdb_score", "imdb_votes", "tmdb_id", "match_confidence", "days_to_streaming",
                "is_trending", "date_added", "source"
            ]
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for r in records:
                    writer.writerow(r)

            # JSON export of 2026 & latest releases
            latest_records = [r for r in records if (r.get("release_year") or 0) >= 2025]
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(latest_records if latest_records else records, f, indent=2, default=str)

        return csv_file, json_file


warehouse_loader = WarehouseLoader()
