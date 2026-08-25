"""Standalone script to download and cache the Kaggle enriched Netflix dataset."""

import sys
from src.extract.historical_loader import HistoricalDatasetLoader
from src.utils.logger import logger


def main() -> None:
    """Download and verify historical dataset."""
    logger.info("Initializing Historical Dataset Download...")
    loader = HistoricalDatasetLoader()
    file_path = loader.download_dataset(force_refresh=True)
    records = loader.load_historical_records(limit=5)
    
    logger.info(f"Successfully cached dataset to: {file_path}")
    logger.info(f"Sample records loaded: {len(records)}")
    for r in records[:3]:
        logger.info(f" - {r['title']} ({r['release_year']}) | IMDb: {r['imdb_score']} | TMDb: {r['tmdb_score']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error downloading historical dataset: {e}")
        sys.exit(1)
