import os
import shutil
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kagglehub
import pandas as pd

from src.utils.logger import logger


def download_and_process():
    logger.info(
        "Downloading dataset 'zohairbaloch/netflix-titles-enriched-with-imdb-and-tmdb' via kagglehub..."
    )
    dataset_dir = kagglehub.dataset_download(
        "zohairbaloch/netflix-titles-enriched-with-imdb-and-tmdb"
    )
    logger.info(f"KaggleHub cached to: {dataset_dir}")

    files = os.listdir(dataset_dir)
    logger.info(f"Files found in dataset: {files}")

    for f in files:
        f_path = os.path.join(dataset_dir, f)
        if os.path.isfile(f_path):
            size_kb = os.path.getsize(f_path) / 1024
            logger.info(f" - {f} ({size_kb:.1f} KB)")
            if f.endswith(".csv"):
                try:
                    df = pd.read_csv(f_path, nrows=5)
                    logger.info(f"   Columns in {f}: {list(df.columns)}")
                except Exception as e:
                    logger.warning(f"   Could not parse {f}: {e}")

    # Look for main titles or combined dataset
    dest_path = os.path.join("data", "raw", "netflix_enriched_historical.csv")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Check if there is a titles.csv or netflix_titles.csv or combined flat CSV
    preferred_files = [
        "titles.csv",
        "netflix_titles_enriched.csv",
        "netflix_titles.csv",
        "netflix_enriched.csv",
    ]
    target_src = None
    for pref in preferred_files:
        candidate = os.path.join(dataset_dir, pref)
        if os.path.exists(candidate):
            target_src = candidate
            break

    if not target_src:
        csv_files = [os.path.join(dataset_dir, f) for f in files if f.endswith(".csv")]
        if csv_files:
            # Pick largest CSV file or first
            csv_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
            target_src = csv_files[0]

    if target_src:
        logger.info(f"Copying {target_src} -> {dest_path}...")
        df_full = pd.read_csv(target_src)
        logger.info(
            f"Total rows in source: {len(df_full):,} | Columns: {list(df_full.columns)}"
        )

        # Ensure standard column mapping if needed
        # Standard columns expected by Power Query & StreamPulse:
        # id, title, type, description, release_year, age_certification, runtime, genres, production_countries, seasons, imdb_id, imdb_score, imdb_votes, tmdb_popularity, tmdb_score

        shutil.copy2(target_src, dest_path)
        logger.info(
            f"[SUCCESS] Updated {dest_path} with full dataset ({len(df_full):,} rows)."
        )
    else:
        logger.error("No CSV files found in downloaded Kaggle dataset.")


if __name__ == "__main__":
    download_and_process()
