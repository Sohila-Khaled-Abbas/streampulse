"""Unit tests for warehouse loader, Parquet lakehouse export, and multi-source file exports."""

import os
import pandas as pd
from src.load.warehouse_loader import WarehouseLoader


def test_warehouse_loader_file_export(tmp_path):
    """Test warehouse loader file and Parquet export mechanism."""
    output_dir = str(tmp_path / "processed")
    loader = WarehouseLoader(output_dir=output_dir)

    sample_records = [
        {
            "netflix_id": "wiki_2026_01",
            "title": "People We Meet on Vacation",
            "media_type": "movie",
            "release_year": 2026,
            "runtime_minutes": 118,
            "maturity_rating": "PG-13",
            "synopsis": "2026 romantic comedy.",
            "vote_average": 7.8,
            "vote_count": 2500,
            "popularity": 120.5,
            "match_confidence": 95.0,
            "days_to_streaming": 9,
            "is_trending": True,
            "date_added": "2026-01-09",
            "source": "wikipedia_2026_films",
        }
    ]

    summary = loader.load_pipeline_records(sample_records, dry_run=True)
    assert summary["total_records"] == 1
    assert os.path.exists(summary["exported_csv"])
    assert os.path.exists(summary["exported_json"])
    assert os.path.exists(summary["exported_parquet"])
    assert os.path.exists(summary["exported_powerbi_parquet"])
    assert os.path.exists(summary["exported_performance_parquet"])
    assert len(summary["lakehouse_tables"]) >= 5

    # Verify Parquet content
    df_parquet = pd.read_parquet(summary["exported_parquet"])
    assert len(df_parquet) == 1
    assert df_parquet["title"].iloc[0] == "People We Meet on Vacation"

    df_pbi = pd.read_parquet(summary["exported_powerbi_parquet"])
    assert len(df_pbi) == 1
    assert df_pbi["catalog_era"].iloc[0] == "2026 Live Releases"
    assert df_pbi["rating_tier"].iloc[0] == "Good (6.5 - 7.9)"

    # Verify Lakehouse tables
    lakehouse_dir = os.path.join(output_dir, "lakehouse")
    assert os.path.exists(os.path.join(lakehouse_dir, "dim_titles.parquet"))
    assert os.path.exists(os.path.join(lakehouse_dir, "dim_genres.parquet"))
    assert os.path.exists(os.path.join(lakehouse_dir, "dim_date.parquet"))
    assert os.path.exists(os.path.join(lakehouse_dir, "fact_catalog_ratings.parquet"))
    assert os.path.exists(os.path.join(lakehouse_dir, "fact_streaming_performance.parquet"))
