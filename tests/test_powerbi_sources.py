"""Unit tests for Power BI Multi-Source dataset conformance and historical catalog validation."""

import json
import os

import pandas as pd
import pytest

from src.extract.historical_loader import HistoricalDatasetLoader
from scripts.prepare_powerbi_sources import prepare_and_verify_all_sources


def test_historical_dataset_integrity():
    """Verify historical dataset meets the 5,800+ benchmark catalog requirement."""
    loader = HistoricalDatasetLoader()
    integrity = loader.validate_integrity()

    assert integrity["is_valid"] is True
    assert integrity["total_records"] >= 5800
    assert integrity["min_release_year"] <= 1960
    assert integrity["max_release_year"] >= 2020
    assert len(integrity["missing_headers"]) == 0
    assert integrity["imdb_scored_titles"] > 4000


def test_imdb_ratings_csv_conformance():
    """Verify Raw_IMDb_Ratings CSV contains all fields expected by Power Query M script."""
    csv_path = os.path.join("data", "raw", "imdb_external_ratings.csv")
    assert os.path.exists(csv_path), "imdb_external_ratings.csv must exist"

    df = pd.read_csv(csv_path)
    expected_cols = [
        "title_id", "imdb_code", "title_name", "user_score",
        "vote_count_raw", "critic_metascore", "snapshot_timestamp"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column '{col}' in IMDb ratings CSV"

    assert len(df) > 0


def test_viewership_parquet_conformance():
    """Verify Raw_Viewership_Parquet contains all fields for Unpivot M script."""
    parquet_path = os.path.join("data", "raw", "streaming_viewership_wide.parquet")
    assert os.path.exists(parquet_path), "streaming_viewership_wide.parquet must exist"

    df = pd.read_parquet(parquet_path)
    expected_cols = [
        "catalog_ref_id", "territory_region", "device_category",
        "Hours_2026_01", "Hours_2026_02", "Hours_2026_03",
        "avg_completion_pct", "subscribers_reached_thousands"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column '{col}' in Viewership Parquet"

    assert len(df) > 0


def test_budget_feed_json_conformance():
    """Verify Raw_Budget_JSON structure for nested expansion in Power Query."""
    json_path = os.path.join("data", "raw", "boxoffice_budget_feed.json")
    assert os.path.exists(json_path), "boxoffice_budget_feed.json must exist"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "data" in data, "JSON feed must have root 'data' array"
    records = data["data"]
    assert len(records) > 0

    first = records[0]
    assert "stream_id" in first
    assert "production_info" in first
    assert "categorization" in first
    assert "genres" in first["categorization"]


def test_prepare_all_sources_pipeline():
    """Test full execution of prepare_and_verify_all_sources."""
    summary = prepare_and_verify_all_sources(force_refresh_historical=False)
    assert summary["source_2_historical_csv"]["status"] == "OK"
    assert summary["source_3_imdb_ratings_csv"]["status"] == "OK"
    assert summary["source_4_viewership_parquet"]["status"] == "OK"
    assert summary["source_5_budget_json"]["status"] == "OK"
    assert summary["lakehouse_exports"]["status"] == "OK"
