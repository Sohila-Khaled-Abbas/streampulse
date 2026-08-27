"""Generates 4 distinct raw multi-source datasets with deliberate data cleaning challenges

for Power BI Power Query (M Language), Data Modeling, and DAX Training.

Sources:
1. PostgreSQL Database (`staging.stg_netflix_titles`) -> Dirty timestamps, non-breaking spaces, text case discrepancies, JSON strings
2. CSV Flat File (`data/raw/imdb_external_ratings.csv`) -> Shorthand votes ('1.2M', '450K'), dirty IDs, out-of-bound ratings, duplicate snapshots
3. Parquet Lakehouse (`data/raw/streaming_viewership_wide.parquet`) -> Wide unpivoted months, country variations ('USA', 'US', 'United States'), sentinel values (-999)
4. JSON REST API Feed (`data/raw/boxoffice_budget_feed.json`) -> Currency symbols ('$150M', '€45 million'), pipe-delimited genres, nested arrays
"""

import csv
import json
import os
import random
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from src.utils.db import db_manager
from src.utils.logger import logger

TITLES_SEED = [
    {"netflix_id": "8001", "canonical": "Avatar: Fire and Ash", "year": 2026, "type": "movie"},
    {"netflix_id": "8002", "canonical": "Stranger Things: The Final Season", "year": 2026, "type": "tv"},
    {"netflix_id": "8003", "canonical": "Avengers: Doomsday", "year": 2026, "type": "movie"},
    {"netflix_id": "8004", "canonical": "Wednesday: Season 2", "year": 2026, "type": "tv"},
    {"netflix_id": "8005", "canonical": "Peaky Blinders: The Immortal Man", "year": 2026, "type": "movie"},
    {"netflix_id": "8006", "canonical": "The Batman Part II", "year": 2026, "type": "movie"},
    {"netflix_id": "8007", "canonical": "Squid Game: The Final Game", "year": 2026, "type": "tv"},
    {"netflix_id": "8008", "canonical": "Dune: Part Three (Messiah)", "year": 2026, "type": "movie"},
    {"netflix_id": "8009", "canonical": "Bridgerton: Season 4", "year": 2026, "type": "tv"},
    {"netflix_id": "8010", "canonical": "Spider-Man: Beyond the Spider-Verse", "year": 2026, "type": "movie"},
    {"netflix_id": "8011", "canonical": "The Mandalorian & Grogu", "year": 2026, "type": "movie"},
    {"netflix_id": "8012", "canonical": "One Piece: Season 2", "year": 2026, "type": "tv"},
    {"netflix_id": "8013", "canonical": "Blade Runner 2099", "year": 2026, "type": "tv"},
    {"netflix_id": "8014", "canonical": "BioShock", "year": 2026, "type": "movie"},
    {"netflix_id": "8015", "canonical": "Gears of War", "year": 2026, "type": "movie"},
    {"netflix_id": "8016", "canonical": "The Witcher: Sirens of the Deep", "year": 2025, "type": "movie"},
    {"netflix_id": "8017", "canonical": "Squid Game: Season 2", "year": 2024, "type": "tv"},
    {"netflix_id": "8018", "canonical": "Dune: Part Two", "year": 2024, "type": "movie"},
    {"netflix_id": "8019", "canonical": "Oppenheimer", "year": 2023, "type": "movie"},
    {"netflix_id": "8020", "canonical": "Red Notice", "year": 2021, "type": "movie"},
]


def generate_source_1_postgres_staging():
    """Seed PostgreSQL staging table with realistic dirty data (text casing, spaces, date formats)."""
    logger.info("Generating Source 1: PostgreSQL staging.stg_netflix_titles (Dirty staging table)...")
    if not db_manager.test_connection():
        logger.warning("PostgreSQL offline; skipping direct DB seed.")
        return

    raw_conn = db_manager.engine.raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staging.stg_netflix_titles (
                    netflix_id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    title_type VARCHAR(50),
                    synopsis TEXT,
                    release_year INT,
                    date_added VARCHAR(100),
                    runtime_seconds VARCHAR(50),
                    maturity_rating VARCHAR(50),
                    raw_json JSONB,
                    extracted_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Dirty data generation patterns
            dirty_staging_rows = []
            for item in TITLES_SEED:
                nid = item["netflix_id"]
                t = item["canonical"]

                # Problem 1: Casing & whitespace quirks
                if nid in ["8001", "8005"]:
                    dirty_title = f"  {t.upper()}  "
                elif nid in ["8003", "8008"]:
                    dirty_title = f"{t.lower()} \xa0"
                else:
                    dirty_title = f" {t} "

                # Problem 2: Mixed date string representations
                date_variations = [
                    "January 15, 2026",
                    "2026-01-15T00:00:00Z",
                    "15/01/2026",
                    "2026.02.01",
                    "2026-03-10",
                    "Invalid Date",
                    "null"
                ]
                dirty_date = date_variations[int(nid) % len(date_variations)]

                # Problem 3: Dirty runtime formats
                runtime_variations = [
                    "5400", "90 mins", "1h 45m", "7200s", "-1", "Unknown", "125 min"
                ]
                dirty_runtime = runtime_variations[int(nid) % len(runtime_variations)]

                # Problem 4: Dirty maturity rating
                rating_variations = ["TV-MA", "tv ma", "R", "PG-13", "pg 13", "18+", "N/A"]
                dirty_rating = rating_variations[int(nid) % len(rating_variations)]

                raw_json = json.dumps({
                    "stream_provider": "Netflix Originals Global",
                    "source_feed": "WebScraper_2026_Live",
                    "ingestion_batch_id": f"BATCH_{nid}_2026",
                    "metadata": {
                        "director_note": "Awaiting final theatrical drop",
                        "audio_tracks": ["en-US", "es-ES", "ja-JP"],
                        "hdr_format": "Dolby Vision"
                    }
                })

                dirty_staging_rows.append((
                    nid, dirty_title, item["type"],
                    f"Official synopsis for {t}. Contains high stakes drama and streaming excitement.",
                    item["year"], dirty_date, dirty_runtime, dirty_rating, raw_json
                ))

            insert_stmt = """
                INSERT INTO staging.stg_netflix_titles (
                    netflix_id, title, title_type, synopsis, release_year,
                    date_added, runtime_seconds, maturity_rating, raw_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (netflix_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    date_added = EXCLUDED.date_added,
                    runtime_seconds = EXCLUDED.runtime_seconds,
                    maturity_rating = EXCLUDED.maturity_rating,
                    raw_json = EXCLUDED.raw_json;
            """
            cursor.executemany(insert_stmt, dirty_staging_rows)
        raw_conn.commit()
        logger.info("Source 1 (PostgreSQL staging) seeded successfully.")
    finally:
        raw_conn.close()


def generate_source_2_csv_imdb_ratings():
    """Generate CSV file with shorthand votes, dirty IDs, and duplicate snapshots."""
    logger.info("Generating Source 2: data/raw/imdb_external_ratings.csv (Dirty CSV)...")
    file_path = os.path.join("data", "raw", "imdb_external_ratings.csv")

    rows = []
    for item in TITLES_SEED:
        nid = item["netflix_id"]

        # Problem 1: Inconsistent ID prefixes
        if int(nid) % 3 == 0:
            imdb_id = f"tt{int(nid)*1000}"
        elif int(nid) % 3 == 1:
            imdb_id = f"IMDB_{int(nid)*1000}"
        else:
            imdb_id = f"{int(nid)*1000}"

        # Problem 2: Shorthand string votes ('1.2M', '450K', '85,420')
        vote_shorthands = ["1.4M", "850K", "45.2K", "120,400", "950", "N/A", "2.1M", "15K"]
        votes = vote_shorthands[int(nid) % len(vote_shorthands)]

        # Problem 3: Out-of-bounds or text ratings ('8.4', '12.5/10', '92%', 'null')
        ratings_dirty = ["8.4", "7.8", "9.1", "12.5/10", "88%", "6.5", "null", "7.9", "8.9"]
        rating = ratings_dirty[int(nid) % len(ratings_dirty)]

        # Problem 4: Match Title with slightly different naming
        matched_title = item["canonical"].replace(":", " -") if ":" in item["canonical"] else item["canonical"]

        # Snapshot 1
        rows.append({
            "title_id": nid,
            "imdb_code": imdb_id,
            "title_name": matched_title,
            "user_score": rating,
            "vote_count_raw": votes,
            "critic_metascore": random.randint(55, 95),
            "review_sentiment": random.choice(["Overwhelmingly Positive", "Positive", "Mixed", "N/A"]),
            "snapshot_timestamp": "2026-02-01 10:00:00"
        })

        # Problem 5: Duplicate Snapshot row with newer timestamp (requires deduplication in Power Query)
        if int(nid) in [8001, 8002, 8003, 8008]:
            rows.append({
                "title_id": nid,
                "imdb_code": imdb_id,
                "title_name": matched_title,
                "user_score": "8.8",
                "vote_count_raw": "1.6M",
                "critic_metascore": 94,
                "review_sentiment": "Universal Acclaim",
                "snapshot_timestamp": "2026-02-15 18:30:00"  # Newer snapshot
            })

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Source 2 CSV generated at {file_path} ({len(rows)} rows).")


def generate_source_3_parquet_viewership():
    """Generate Parquet file in wide unpivoted format with country anomalies and sentinel values."""
    logger.info("Generating Source 3: data/raw/streaming_viewership_wide.parquet (Dirty Wide Parquet)...")
    file_path = os.path.join("data", "raw", "streaming_viewership_wide.parquet")

    records = []
    countries = ["USA", "US", "United States", "u.s.a.", "UK", "GBR", "Great Britain", "South Korea", "KOR", "Japan", "JPN", "Germany", "DEU", "Global"]

    for item in TITLES_SEED:
        nid = item["netflix_id"]

        # Problem 1: Country code inconsistencies
        c_choice = countries[int(nid) % len(countries)]

        # Problem 2: Wide format columns (Jan, Feb, Mar 2026 view hours) requiring Unpivot in Power Query
        # Problem 3: Sentinel negative values (-999, -1) representing missing telemetry
        jan_hours = round(random.uniform(5.0, 45.0), 2) if int(nid) != 8005 else -999.0
        feb_hours = round(random.uniform(8.0, 60.0), 2) if int(nid) != 8009 else -1.0
        mar_hours = round(random.uniform(10.0, 75.0), 2)

        completion_pct = round(random.uniform(60.0, 95.0), 1) if int(nid) != 8014 else 150.0  # Out of range 150%

        records.append({
            "catalog_ref_id": nid,
            "title_alias": item["canonical"],
            "territory_region": c_choice,
            "device_category": random.choice(["Smart TV", "Mobile", "Web Browser", "Console", "Tablet"]),
            "Hours_2026_01": jan_hours,
            "Hours_2026_02": feb_hours,
            "Hours_2026_03": mar_hours,
            "avg_completion_pct": completion_pct,
            "subscribers_reached_thousands": random.randint(500, 15000),
            "data_quality_flag": "RAW_TELEMETRY"
        })

    df = pd.DataFrame(records)
    df.to_parquet(file_path, engine="pyarrow", index=False, compression="snappy")
    logger.info(f"Source 3 Parquet generated at {file_path} ({len(df)} rows).")


def generate_source_4_json_budget_feed():
    """Generate JSON file with dirty currency formats, pipe-delimited genres, and nested structures."""
    logger.info("Generating Source 4: data/raw/boxoffice_budget_feed.json (Dirty JSON Feed)...")
    file_path = os.path.join("data", "raw", "boxoffice_budget_feed.json")

    feed_data = []
    for item in TITLES_SEED:
        nid = item["netflix_id"]
        t = item["canonical"]

        # Problem 1: Dirty currency and text budget formats
        budget_strings = [
            "$150,000,000",
            "$200M",
            "€45 million",
            "£25.5M",
            "$45,000,000 (est.)",
            "Unknown",
            "N/A",
            "$80 million",
            "$300M"
        ]
        dirty_budget = budget_strings[int(nid) % len(budget_strings)]

        # Problem 2: Pipe-delimited genre string vs nested list
        if int(nid) % 2 == 0:
            genres_obj = "Action|Sci-Fi|Adventure"
        else:
            genres_obj = ["Drama", "Thriller", "Crime"]

        # Problem 3: Dirty worldwide box office / SVOD revenue
        revenue_values = [
            "$1.2 Billion", "$450,000,000", "€120M", "N/A - Direct to SVOD", "$850.5M", "TBD"
        ]
        dirty_rev = revenue_values[int(nid) % len(revenue_values)]

        feed_data.append({
            "stream_id": nid,
            "production_info": {
                "title": t,
                "studio": random.choice(["Warner Bros.", "Paramount", "Netflix Studios", "A24", "Universal", "Sony Pictures"]),
                "producer": random.choice(["Jerry Bruckheimer", "Kathleen Kennedy", "Jason Blum", "Emma Thomas", "Kevin Feige"]),
                "production_budget_raw": dirty_budget,
                "worldwide_gross_raw": dirty_rev,
            },
            "categorization": {
                "genres": genres_obj,
                "content_warnings": ["Violence", "Language", "Flashing Lights"] if int(nid) % 3 == 0 else []
            },
            "financial_roi_tier": random.choice(["Blockbuster Hit", "Profitable", "Break Even", "Underperformer", "Unreported"]),
            "last_synced_utc": "2026-02-27T19:00:00Z"
        })

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"api_version": "v2.6", "total_records": len(feed_data), "data": feed_data}, f, indent=2)

    logger.info(f"Source 4 JSON generated at {file_path} ({len(feed_data)} items).")


def run_all():
    """Generate all 4 distinct raw datasets."""
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    generate_source_1_postgres_staging()
    generate_source_2_csv_imdb_ratings()
    generate_source_3_parquet_viewership()
    generate_source_4_json_budget_feed()
    logger.info("All 4 distinct raw training datasets generated successfully!")


if __name__ == "__main__":
    run_all()
