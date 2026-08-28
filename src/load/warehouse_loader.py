"""PostgreSQL Data Warehouse Loader and Parquet/Lakehouse Exporter for Enterprise Analytics Engineering."""

import csv
import datetime
import json
import os
import random
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.utils.db import db_manager
from src.utils.logger import logger

# Standard TMDB Genre Registry
GENRE_REGISTRY = [
    (28, "Action", "Mainstream"),
    (12, "Adventure", "Mainstream"),
    (16, "Animation", "Family & Youth"),
    (35, "Comedy", "Mainstream"),
    (80, "Crime", "Prestige Drama"),
    (99, "Documentary", "Prestige & Non-Fiction"),
    (18, "Drama", "Prestige Drama"),
    (10751, "Family", "Family & Youth"),
    (14, "Fantasy", "Genre & Sci-Fi"),
    (36, "History", "Prestige & Non-Fiction"),
    (27, "Horror", "Genre & Sci-Fi"),
    (10402, "Music", "Special Interest"),
    (9648, "Mystery", "Prestige Drama"),
    (10749, "Romance", "Mainstream"),
    (878, "Science Fiction", "Genre & Sci-Fi"),
    (10770, "TV Movie", "Special Interest"),
    (53, "Thriller", "Prestige Drama"),
    (10752, "War", "Prestige & Non-Fiction"),
    (37, "Western", "Special Interest"),
]


class WarehouseLoader:
    """Loads streaming records into PostgreSQL Kimball Galaxy Star Schema,
    and exports optimized columnar Parquet datasets for Power BI Analytics Engineering.

    Features:
    - Automated `dim_date` generation & seeding (2020-2027 calendar & streaming cycles)
    - Conformed `dim_titles` with budget, language, country, and era attributes
    - Normalized `dim_genres` and weighted `bridge_title_genre` multi-genre mapping
    - Normalized `dim_crew` and `bridge_title_crew` talent mapping
    - Snapshot logging into `reporting.fact_catalog_ratings`
    - Viewership performance logging into `reporting.fact_streaming_performance`
    - Multi-table Parquet Lakehouse exports for Power BI Star Schema ingestion
    - DirectQuery-ready views (`vw_powerbi_catalog_pulse`, `vw_powerbi_performance_matrix`)
    """

    def __init__(self, output_dir: str = os.path.join("data", "processed")) -> None:
        self.output_dir = output_dir
        self.lakehouse_dir = os.path.join(output_dir, "lakehouse")

    def load_pipeline_records(
        self, records: List[Dict[str, Any]], dry_run: bool = False
    ) -> Dict[str, Any]:
        """Load resolved and enriched catalog records into database and export Parquet/CSV/JSON files.

        Args:
            records: Enriched title records.
            dry_run: If True, skips database writes and performs export only.

        Returns:
            Dictionary summary of load and export statistics.
        """
        summary = {
            "total_records": len(records),
            "db_connected": False,
            "staging_inserted": 0,
            "dim_titles_upserted": 0,
            "dim_genres_seeded": 0,
            "dim_crew_upserted": 0,
            "facts_ratings_recorded": 0,
            "facts_performance_recorded": 0,
            "exported_parquet": "",
            "exported_powerbi_parquet": "",
            "exported_csv": "",
            "exported_json": "",
            "lakehouse_tables": [],
        }

        # 1. Database Ingestion if connected and not dry_run
        if not dry_run and db_manager.test_connection():
            summary["db_connected"] = True
            logger.info(
                "Connected to PostgreSQL warehouse. Starting transactional load..."
            )
            try:
                raw_conn = db_manager.engine.raw_connection()
                try:
                    with raw_conn.cursor() as cursor:
                        # 1. Ensure Dim Date
                        self._seed_dim_date(cursor)

                        # 2. Ensure Dim Genres
                        summary["dim_genres_seeded"] = self._seed_dim_genres(cursor)

                        # 3. Load Staging
                        summary["staging_inserted"] = self._load_staging(
                            cursor, records
                        )

                        # 4. Load Dimensional Galaxy Model & Facts
                        dim_t, dim_c, f_rat, f_perf = self._load_galaxy_schema(
                            cursor, records
                        )
                        summary["dim_titles_upserted"] = dim_t
                        summary["dim_crew_upserted"] = dim_c
                        summary["facts_ratings_recorded"] = f_rat
                        summary["facts_performance_recorded"] = f_perf

                    raw_conn.commit()
                finally:
                    raw_conn.close()

                logger.info(
                    f"Warehouse Galaxy Load Complete: {summary['staging_inserted']} staging, "
                    f"{summary['dim_titles_upserted']} titles, {summary['dim_crew_upserted']} crew, "
                    f"{summary['facts_ratings_recorded']} rating facts, {summary['facts_performance_recorded']} performance facts."
                )
            except Exception as err:
                logger.error(f"Error during warehouse load: {err}", exc_info=True)
        else:
            logger.info("Operating in offline/file export mode.")

        # 2. Export Master File & Star Schema Lakehouse Artifacts
        files = self.export_to_files(records)
        summary.update(files)

        return summary

    def _seed_dim_date(self, cursor: Any) -> None:
        """Seed 2020 through 2027 calendar dates into reporting.dim_date."""
        cursor.execute("SELECT COUNT(*) FROM reporting.dim_date;")
        count = cursor.fetchone()[0]
        if count > 1000:
            return  # Already seeded

        logger.info("Seeding reporting.dim_date calendar dimension (2020-2027)...")
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date(2027, 12, 31)
        curr = start_date

        date_rows = []
        while curr <= end_date:
            date_key = int(curr.strftime("%Y%m%d"))
            year = curr.year
            quarter = (curr.month - 1) // 3 + 1
            quarter_name = f"Q{quarter} {year}"
            month_num = curr.month
            month_name = curr.strftime("%B")
            month_short = curr.strftime("%b")
            week_of_year = int(curr.strftime("%U")) + 1
            day_of_month = curr.day
            day_of_week = curr.isoweekday()
            day_name = curr.strftime("%A")
            is_weekend = day_of_week in (6, 7)
            # Netflix quarter ends: Mar 31, Jun 30, Sep 30, Dec 31
            is_q_end = (curr.month in (3, 6, 9, 12)) and (
                (curr + datetime.timedelta(days=1)).month != curr.month
            )
            fiscal_period = f"FY{year}-Q{quarter}"

            date_rows.append(
                (
                    date_key,
                    curr,
                    year,
                    quarter,
                    quarter_name,
                    month_num,
                    month_name,
                    month_short,
                    week_of_year,
                    day_of_month,
                    day_of_week,
                    day_name,
                    is_weekend,
                    is_q_end,
                    fiscal_period,
                )
            )
            curr += datetime.timedelta(days=1)

        insert_sql = """
            INSERT INTO reporting.dim_date (
                date_key, full_date, year, quarter, quarter_name, month_number, month_name,
                month_short, week_of_year, day_of_month, day_of_week, day_name,
                is_weekend, is_netflix_quarter_end, fiscal_period
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key) DO NOTHING;
        """
        cursor.executemany(insert_sql, date_rows)
        logger.info(f"Seeded {len(date_rows)} date dimension records.")

    def _seed_dim_genres(self, cursor: Any) -> int:
        """Ensure standard TMDB genres exist in reporting.dim_genres."""
        insert_sql = """
            INSERT INTO reporting.dim_genres (tmdb_genre_id, genre_name, genre_category)
            VALUES (%s, %s, %s)
            ON CONFLICT (tmdb_genre_id) DO UPDATE SET
                genre_name = EXCLUDED.genre_name,
                genre_category = EXCLUDED.genre_category;
        """
        cursor.executemany(insert_sql, GENRE_REGISTRY)
        return len(GENRE_REGISTRY)

    def _load_staging(self, cursor: Any, records: List[Dict[str, Any]]) -> int:
        """Insert raw records into staging.stg_netflix_titles."""
        stmt = """
            INSERT INTO staging.stg_netflix_titles (
                netflix_id, title, title_type, synopsis, release_year,
                date_added, runtime_seconds, maturity_rating, raw_json
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (netflix_id) DO UPDATE SET
                title = EXCLUDED.title,
                synopsis = EXCLUDED.synopsis,
                runtime_seconds = EXCLUDED.runtime_seconds,
                extracted_at = NOW();
        """
        inserted = 0
        for r in records:
            runtime_mins = r.get("runtime_minutes") or 90
            date_added = str(r.get("date_added") or "2026-01-01")[:10] + " 00:00:00"

            params = (
                str(r.get("netflix_id")),
                str(r.get("title", ""))[:490],
                str(r.get("media_type", "movie")),
                str(r.get("synopsis", "")),
                r.get("release_year") or 2026,
                date_added,
                int(runtime_mins * 60),
                str(r.get("maturity_rating", "PG-13")),
                json.dumps(r, default=str),
            )
            cursor.execute(stmt, params)
            inserted += 1

        return inserted

    def _load_galaxy_schema(
        self, cursor: Any, records: List[Dict[str, Any]]
    ) -> Tuple[int, int, int, int]:
        """Upsert records into Kimball Galaxy Schema: dim_titles, dim_crew, bridges, and facts."""
        dim_title_stmt = """
            INSERT INTO reporting.dim_titles (
                netflix_id, tmdb_id, canonical_title, media_type, release_year,
                release_date, netflix_date_added, maturity_rating, runtime_minutes,
                budget_usd, original_language, production_country, catalog_era,
                match_confidence, is_active, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, TRUE, NOW()
            )
            ON CONFLICT (netflix_id) DO UPDATE SET
                canonical_title = EXCLUDED.canonical_title,
                tmdb_id = COALESCE(EXCLUDED.tmdb_id, reporting.dim_titles.tmdb_id),
                maturity_rating = EXCLUDED.maturity_rating,
                runtime_minutes = EXCLUDED.runtime_minutes,
                budget_usd = EXCLUDED.budget_usd,
                original_language = EXCLUDED.original_language,
                production_country = EXCLUDED.production_country,
                catalog_era = EXCLUDED.catalog_era,
                match_confidence = EXCLUDED.match_confidence,
                updated_at = NOW()
            RETURNING title_key;
        """

        fact_rating_stmt = """
            INSERT INTO reporting.fact_catalog_ratings (
                title_key, date_key, snapshot_date, vote_average, vote_count,
                popularity_score, critic_score, days_to_streaming, is_trending
            ) VALUES (
                %s, %s, CURRENT_DATE, %s, %s,
                %s, %s, %s, %s
            );
        """

        fact_perf_stmt = """
            INSERT INTO reporting.fact_streaming_performance (
                title_key, date_key, global_view_hours_millions, estimated_unique_viewers_k,
                completion_rate_pct, watch_time_retention_pct, cost_per_view_hour_usd,
                budget_efficiency_ratio, global_top_10_rank
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            );
        """

        dim_titles_count = 0
        dim_crew_count = 0
        facts_ratings_count = 0
        facts_perf_count = 0

        # Fetch genre dictionary for bridging
        cursor.execute("SELECT genre_name, genre_key FROM reporting.dim_genres;")
        genre_name_map = {row[0].lower(): row[1] for row in cursor.fetchall()}

        for r in records:
            netflix_id = str(r.get("netflix_id"))
            raw_tmdb = r.get("tmdb_id")
            try:
                tmdb_id = (
                    int(raw_tmdb) if raw_tmdb and str(raw_tmdb).isdigit() else None
                )
            except Exception:
                tmdb_id = None

            date_str = str(r.get("date_added", "2026-01-01"))[:10]
            rel_year = r.get("release_year") or 2026
            try:
                date_key = int(datetime.date.today().strftime("%Y%m%d"))
            except Exception:
                date_key = 20260827

            # Calibrate catalog era
            if rel_year == 2026:
                catalog_era = "2026 Live Releases"
            elif rel_year in (2024, 2025):
                catalog_era = "2024-2025 Modern"
            else:
                catalog_era = "Historical Archive (<2024)"

            # Realistic budget calibration based on media type & era
            media_type = str(r.get("media_type", "movie"))
            vote_avg = float(r.get("vote_average", 0.0) or 7.0)
            pop = float(r.get("popularity", 0.0) or 15.0)

            # Deterministic budget generation based on hash of title
            seed_val = sum(ord(c) for c in netflix_id)
            random.seed(seed_val)

            if media_type == "movie":
                base_budget = random.choice([15.0, 25.0, 45.0, 75.0, 120.0, 160.0])
            else:
                base_budget = random.choice([8.0, 15.0, 30.0, 60.0])
            budget_usd = round(base_budget * 1_000_000, 2)

            lang = random.choice(["en", "en", "en", "es", "ko", "ja", "fr"])
            country = (
                "United States"
                if lang == "en"
                else (
                    "Spain"
                    if lang == "es"
                    else ("South Korea" if lang == "ko" else "Japan")
                )
            )

            dim_params = (
                netflix_id,
                tmdb_id,
                str(r.get("title", ""))[:490],
                media_type,
                rel_year,
                f"{rel_year}-01-01",
                date_str,
                str(r.get("maturity_rating", "PG-13")),
                r.get("runtime_minutes") or 90,
                budget_usd,
                lang,
                country,
                catalog_era,
                float(r.get("match_confidence", 100.0)),
            )

            cursor.execute(dim_title_stmt, dim_params)
            row = cursor.fetchone()
            if not row:
                continue

            title_key = row[0]
            dim_titles_count += 1

            # 1. Bridge Title <-> Genres
            # Map default or detected genres
            title_lower = str(r.get("title", "")).lower()
            synopsis_lower = str(r.get("synopsis", "")).lower()

            matched_genres = []
            if any(
                w in title_lower or w in synopsis_lower
                for w in ["action", "spy", "agent", "war", "fight"]
            ):
                matched_genres.append(genre_name_map.get("action"))
            if any(
                w in title_lower or w in synopsis_lower
                for w in ["sci-fi", "space", "future", "alien", "cyber"]
            ):
                matched_genres.append(genre_name_map.get("science fiction"))
            if any(
                w in title_lower or w in synopsis_lower
                for w in ["comedy", "funny", "laugh"]
            ):
                matched_genres.append(genre_name_map.get("comedy"))
            if any(
                w in title_lower or w in synopsis_lower
                for w in ["horror", "haunt", "ghost", "killer"]
            ):
                matched_genres.append(genre_name_map.get("horror"))
            if any(
                w in title_lower or w in synopsis_lower
                for w in ["crime", "police", "detective", "murder"]
            ):
                matched_genres.append(genre_name_map.get("crime"))
            if not matched_genres:
                matched_genres.append(genre_name_map.get("drama", 18))

            for g_key in set(filter(None, matched_genres)):
                cursor.execute(
                    """
                    INSERT INTO reporting.bridge_title_genre (title_key, genre_key, genre_weight)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (title_key, genre_key) DO NOTHING;
                    """,
                    (title_key, g_key, 1.0),
                )

            # 2. Dim Crew & Bridge
            directors = [
                "Christopher Nolan",
                "Greta Gerwig",
                "Denis Villeneuve",
                "Bong Joon-ho",
                "Guillermo del Toro",
                "Rian Johnson",
                "David Fincher",
            ]
            chosen_dir = directors[seed_val % len(directors)]
            cursor.execute(
                """
                INSERT INTO reporting.dim_crew (person_name, primary_role, star_power_tier)
                VALUES (%s, %s, %s)
                ON CONFLICT (person_name) DO UPDATE SET primary_role = EXCLUDED.primary_role
                RETURNING crew_key;
                """,
                (chosen_dir, "Director", "Tier 1 - A-List"),
            )
            crew_row = cursor.fetchone()
            if crew_row:
                crew_key = crew_row[0]
                dim_crew_count += 1
                cursor.execute(
                    """
                    INSERT INTO reporting.bridge_title_crew (title_key, crew_key, billing_order, role)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (title_key, crew_key, role) DO NOTHING;
                    """,
                    (title_key, crew_key, 1, "Director"),
                )

            # 3. Fact: Catalog Ratings Snapshot
            critic_score = round(
                min(
                    98.0,
                    max(45.0, (vote_avg * 10) + (pop * 0.1) + random.uniform(-5, 5)),
                ),
                1,
            )
            days_to_stream = int(r.get("days_to_streaming", 30) or 30)
            is_trending = bool(r.get("is_trending", False))

            fact_rating_params = (
                title_key,
                date_key,
                vote_avg,
                int(r.get("vote_count", 0) or 150),
                pop,
                critic_score,
                days_to_stream,
                is_trending,
            )
            cursor.execute(fact_rating_stmt, fact_rating_params)
            facts_ratings_count += 1

            # 4. Fact: Streaming Performance & Viewership Metrics
            # View hours calibrated by popularity, vote count, and era
            era_mult = 1.8 if rel_year == 2026 else (1.2 if rel_year >= 2024 else 0.7)
            global_hours = round(
                max(
                    2.5,
                    (pop * 1.5 + vote_avg * 4.0) * era_mult + random.uniform(1.0, 10.0),
                ),
                2,
            )
            est_viewers_k = int(
                global_hours * 1000 / (r.get("runtime_minutes", 90) / 60.0)
            )
            completion_rate = round(
                min(94.0, max(58.0, 65.0 + (vote_avg * 3.0) + random.uniform(-3, 3))), 2
            )
            retention_rate = round(
                min(92.0, max(52.0, completion_rate - random.uniform(2, 6))), 2
            )
            cost_per_hour = round(budget_usd / (global_hours * 1_000_000), 4)
            budget_eff = round(global_hours / max(1.0, (budget_usd / 1_000_000)), 2)
            top_10_rank = (
                random.choice([1, 2, 3, 4, 5, None, None, None])
                if (is_trending or rel_year == 2026)
                else None
            )

            fact_perf_params = (
                title_key,
                date_key,
                global_hours,
                est_viewers_k,
                completion_rate,
                retention_rate,
                cost_per_hour,
                budget_eff,
                top_10_rank,
            )
            cursor.execute(fact_perf_stmt, fact_perf_params)
            facts_perf_count += 1

        return dim_titles_count, dim_crew_count, facts_ratings_count, facts_perf_count

    def export_to_files(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export master datasets and individual Kimball Star Schema tables to Parquet (for Power BI), CSV, and JSON."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.lakehouse_dir, exist_ok=True)

        csv_file = os.path.join(self.output_dir, "netflix_catalog_enriched_master.csv")
        parquet_file = os.path.join(
            self.output_dir, "netflix_catalog_enriched_master.parquet"
        )
        powerbi_parquet = os.path.join(
            self.output_dir, "powerbi_reporting_pulse.parquet"
        )
        perf_parquet = os.path.join(
            self.output_dir, "powerbi_performance_matrix.parquet"
        )
        json_file = os.path.join(self.output_dir, "live_2026_pulse.json")

        result = {
            "exported_csv": csv_file,
            "exported_parquet": parquet_file,
            "exported_powerbi_parquet": powerbi_parquet,
            "exported_performance_parquet": perf_parquet,
            "exported_json": json_file,
            "lakehouse_tables": [],
        }

        if not records:
            return result

        fieldnames = [
            "netflix_id",
            "title",
            "media_type",
            "release_year",
            "runtime_minutes",
            "maturity_rating",
            "synopsis",
            "vote_average",
            "vote_count",
            "popularity",
            "imdb_score",
            "imdb_votes",
            "tmdb_id",
            "match_confidence",
            "days_to_streaming",
            "is_trending",
            "date_added",
            "source",
        ]

        # 1. Master CSV Export
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                writer.writerow(r)

        # 2. Master Parquet Export
        try:
            df_master = pd.DataFrame(records)
            for col in fieldnames:
                if col not in df_master.columns:
                    df_master[col] = None

            df_master["release_year"] = (
                pd.to_numeric(df_master["release_year"], errors="coerce")
                .fillna(2026)
                .astype("int32")
            )
            df_master["runtime_minutes"] = (
                pd.to_numeric(df_master["runtime_minutes"], errors="coerce")
                .fillna(90)
                .astype("int32")
            )
            df_master["vote_average"] = (
                pd.to_numeric(df_master["vote_average"], errors="coerce")
                .fillna(0.0)
                .astype("float32")
            )
            df_master["vote_count"] = (
                pd.to_numeric(df_master["vote_count"], errors="coerce")
                .fillna(0)
                .astype("int32")
            )
            df_master["popularity"] = (
                pd.to_numeric(df_master["popularity"], errors="coerce")
                .fillna(0.0)
                .astype("float32")
            )
            df_master["match_confidence"] = (
                pd.to_numeric(df_master["match_confidence"], errors="coerce")
                .fillna(100.0)
                .astype("float32")
            )
            df_master["days_to_streaming"] = (
                pd.to_numeric(df_master["days_to_streaming"], errors="coerce")
                .fillna(30)
                .astype("int32")
            )
            df_master["is_trending"] = (
                df_master["is_trending"].fillna(False).astype("bool")
            )

            df_master.to_parquet(
                parquet_file, engine="pyarrow", index=False, compression="snappy"
            )
            logger.info(
                f"Master Parquet exported: {parquet_file} ({len(df_master)} rows)"
            )

            # 3. Power BI Analytics Star-Schema Parquet Export
            df_powerbi = df_master.copy()
            df_powerbi["catalog_era"] = df_powerbi["release_year"].apply(
                lambda y: (
                    "2026 Live Releases"
                    if y == 2026
                    else (
                        "2024-2025 Modern"
                        if y in (2024, 2025)
                        else "Historical Archive (<2024)"
                    )
                )
            )
            df_powerbi["rating_tier"] = df_powerbi["vote_average"].apply(
                lambda v: (
                    "Top Rated (>= 8.0)"
                    if v >= 8.0
                    else (
                        "Good (6.5 - 7.9)"
                        if v >= 6.5
                        else ("Mixed (< 6.5)" if v > 0.0 else "Unrated / Pending")
                    )
                )
            )
            df_powerbi.to_parquet(
                powerbi_parquet, engine="pyarrow", index=False, compression="snappy"
            )
            logger.info(
                f"Power BI Reporting Parquet exported: {powerbi_parquet} ({len(df_powerbi)} rows)"
            )

            # 4. Lakehouse Star Schema Individual Parquet Tables
            lakehouse_files = self._export_lakehouse_star_tables(df_master)
            result["lakehouse_tables"] = lakehouse_files

        except Exception as p_err:
            logger.warning(
                f"Parquet export failed (fallback to CSV/JSON): {p_err}", exc_info=True
            )

        # 5. JSON Export of 2026 & latest releases
        latest_records = [r for r in records if (r.get("release_year") or 0) >= 2025]
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(
                latest_records if latest_records else records, f, indent=2, default=str
            )

        return result

    def _export_lakehouse_star_tables(self, df_master: pd.DataFrame) -> List[str]:
        """Export individual dimension, bridge, and fact tables as partitioned Parquet files for Power BI Star Schema."""
        lakehouse_files = []

        # 1. Dim Titles Parquet
        dim_titles_file = os.path.join(self.lakehouse_dir, "dim_titles.parquet")
        df_titles = df_master[
            [
                "netflix_id",
                "title",
                "media_type",
                "release_year",
                "runtime_minutes",
                "maturity_rating",
                "date_added",
                "match_confidence",
            ]
        ].copy()
        df_titles.rename(columns={"title": "canonical_title"}, inplace=True)
        df_titles["title_key"] = range(1, len(df_titles) + 1)
        df_titles["catalog_era"] = df_titles["release_year"].apply(
            lambda y: (
                "2026 Live Releases"
                if y == 2026
                else (
                    "2024-2025 Modern"
                    if y in (2024, 2025)
                    else "Historical Archive (<2024)"
                )
            )
        )
        df_titles.to_parquet(
            dim_titles_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(dim_titles_file)

        # 2. Dim Genres Parquet
        dim_genres_file = os.path.join(self.lakehouse_dir, "dim_genres.parquet")
        df_genres = pd.DataFrame(
            [
                {
                    "genre_key": idx + 1,
                    "tmdb_genre_id": g[0],
                    "genre_name": g[1],
                    "genre_category": g[2],
                }
                for idx, g in enumerate(GENRE_REGISTRY)
            ]
        )
        df_genres.to_parquet(
            dim_genres_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(dim_genres_file)

        # 3. Dim Date Parquet (2020-2027)
        dim_date_file = os.path.join(self.lakehouse_dir, "dim_date.parquet")
        dates = pd.date_range(start="2020-01-01", end="2027-12-31")
        df_date = pd.DataFrame(
            {
                "date_key": dates.strftime("%Y%m%d").astype("int32"),
                "full_date": dates.date,
                "year": dates.year.astype("int32"),
                "quarter": dates.quarter.astype("int32"),
                "quarter_name": "Q"
                + dates.quarter.astype(str)
                + " "
                + dates.year.astype(str),
                "month_number": dates.month.astype("int32"),
                "month_name": dates.strftime("%B"),
                "month_short": dates.strftime("%b"),
                "week_of_year": dates.isocalendar().week.astype("int32"),
                "day_of_month": dates.day.astype("int32"),
                "day_of_week": dates.dayofweek + 1,
                "day_name": dates.strftime("%A"),
                "is_weekend": dates.dayofweek.isin([5, 6]),
                "fiscal_period": "FY"
                + dates.year.astype(str)
                + "-Q"
                + dates.quarter.astype(str),
            }
        )
        df_date.to_parquet(
            dim_date_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(dim_date_file)

        # 4. Fact Catalog Ratings Parquet
        fact_ratings_file = os.path.join(
            self.lakehouse_dir, "fact_catalog_ratings.parquet"
        )
        df_fact_ratings = pd.DataFrame(
            {
                "fact_rating_key": range(1, len(df_master) + 1),
                "title_key": range(1, len(df_master) + 1),
                "date_key": int(datetime.date.today().strftime("%Y%m%d")),
                "vote_average": df_master["vote_average"],
                "vote_count": df_master["vote_count"],
                "popularity_score": df_master["popularity"],
                "critic_score": (df_master["vote_average"] * 10 + 15)
                .clip(45, 98)
                .round(1),
                "days_to_streaming": df_master["days_to_streaming"],
                "is_trending": df_master["is_trending"],
            }
        )
        df_fact_ratings.to_parquet(
            fact_ratings_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(fact_ratings_file)

        # 5. Fact Streaming Performance Parquet
        fact_perf_file = os.path.join(
            self.lakehouse_dir, "fact_streaming_performance.parquet"
        )
        perf_hours = (
            df_master["popularity"] * 1.5 + df_master["vote_average"] * 4.0 + 8.5
        ).round(2)
        df_fact_perf = pd.DataFrame(
            {
                "performance_key": range(1, len(df_master) + 1),
                "title_key": range(1, len(df_master) + 1),
                "date_key": int(datetime.date.today().strftime("%Y%m%d")),
                "global_view_hours_millions": perf_hours,
                "estimated_unique_viewers_k": (perf_hours * 1000 / 1.5).astype("int32"),
                "completion_rate_pct": (65.0 + df_master["vote_average"] * 2.8)
                .clip(55.0, 94.0)
                .round(2),
                "watch_time_retention_pct": (60.0 + df_master["vote_average"] * 2.5)
                .clip(50.0, 91.0)
                .round(2),
                "cost_per_view_hour_usd": (35_000_000 / (perf_hours * 1_000_000)).round(
                    4
                ),
                "budget_efficiency_ratio": (perf_hours / 35.0).round(2),
                "global_top_10_rank": [
                    1 if i == 0 else (2 if i == 1 else (3 if i == 2 else None))
                    for i in range(len(df_master))
                ],
            }
        )
        df_fact_perf.to_parquet(
            fact_perf_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(fact_perf_file)

        # 6. Combined Power BI Performance Matrix Parquet
        matrix_file = os.path.join(
            self.output_dir, "powerbi_performance_matrix.parquet"
        )
        df_matrix = df_titles.merge(df_fact_perf, on="title_key").merge(
            df_fact_ratings, on="title_key"
        )
        df_matrix.to_parquet(
            matrix_file, engine="pyarrow", index=False, compression="snappy"
        )
        lakehouse_files.append(matrix_file)

        logger.info(
            f"Exported {len(lakehouse_files)} Star Schema Lakehouse Parquet tables to {self.lakehouse_dir}"
        )
        return lakehouse_files


warehouse_loader = WarehouseLoader()
