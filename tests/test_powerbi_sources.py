"""Offline conformance checks for the generated Power BI training source formats.

The pipeline exports generated files into ignored data/raw/. A fresh CI checkout
contains no such files, so these tests create their own isolated inputs.
"""
import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import prepare_powerbi_sources
from src.extract.generate_dirty_training_datasets import (
    generate_source_2_csv_imdb_ratings,
    generate_source_3_parquet_viewership,
    generate_source_4_json_budget_feed,
)
from src.extract.historical_loader import HistoricalDatasetLoader


@pytest.fixture
def prepared_sources(tmp_path, monkeypatch):
    """Create representative raw inputs without DB access or external HTTP calls."""
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)

    # A deterministic *synthetic test fixture*, not an actual Kaggle snapshot.
    # Real Kaggle/mirror catalog sizes differ and must be reported honestly.
    historical = raw / "netflix_enriched_historical.csv"
    with historical.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "title", "release_year", "imdb_score", "tmdb_score"])
        for i in range(5100):
            writer.writerow(
                [f"fixture_{i}", f"Unit test title {i}", 1950 if i == 0 else 2022,
                 "7.5" if i < 4500 else "", "7.1"]
            )

    # Generate only file-based training sources, never mutate a real warehouse.
    generate_source_2_csv_imdb_ratings()
    generate_source_3_parquet_viewership()
    generate_source_4_json_budget_feed()
    return raw


def test_historical_dataset_integrity(prepared_sources):
    """Validate the loader's documented minimum 5,000-row integrity contract."""
    loader = HistoricalDatasetLoader(
        cache_path=str(prepared_sources / "netflix_enriched_historical.csv")
    )
    integrity = loader.validate_integrity()
    assert integrity["is_valid"] is True
    assert integrity["total_records"] == 5100
    assert integrity["min_release_year"] <= 1960
    assert integrity["max_release_year"] >= 2020
    assert integrity["imdb_scored_titles"] == 4500


def test_imdb_ratings_csv_conformance(prepared_sources):
    df = pd.read_csv(prepared_sources / "imdb_external_ratings.csv")
    expected_cols = {
        "title_id", "imdb_code", "title_name", "user_score",
        "vote_count_raw", "critic_metascore", "snapshot_timestamp",
    }
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_viewership_parquet_conformance(prepared_sources):
    df = pd.read_parquet(prepared_sources / "streaming_viewership_wide.parquet")
    expected_cols = {
        "catalog_ref_id", "territory_region", "device_category",
        "Hours_2026_01", "Hours_2026_02", "Hours_2026_03",
        "avg_completion_pct", "subscribers_reached_thousands",
    }
    assert expected_cols.issubset(df.columns)
    assert not df.empty


def test_budget_feed_json_conformance(prepared_sources):
    with (prepared_sources / "boxoffice_budget_feed.json").open(
        encoding="utf-8"
    ) as file:
        feed = json.load(file)
    assert isinstance(feed.get("data"), list) and feed["data"]
    first = feed["data"][0]
    assert {"stream_id", "production_info", "categorization"}.issubset(first)
    assert "genres" in first["categorization"]


def test_prepare_all_sources_pipeline(prepared_sources, monkeypatch):
    """Validate file preparation while isolating external network and DB side effects."""
    monkeypatch.setattr(
        prepare_powerbi_sources.db_manager, "test_connection", lambda: False
    )
    monkeypatch.setattr(
        prepare_powerbi_sources, "run_pipeline_step",
        lambda **kwargs: {
            "load_summary": {
                "lakehouse_tables": ["fixture_dim_titles"],
                "exported_csv": "fixture.csv",
                "exported_parquet": "fixture.parquet",
            }
        },
    )
    summary = prepare_powerbi_sources.prepare_and_verify_all_sources(
        force_refresh_historical=False
    )
    assert summary["source_2_historical_csv"]["status"] == "OK"
    assert summary["source_3_imdb_ratings_csv"]["status"] == "OK"
    assert summary["source_4_viewership_parquet"]["status"] == "OK"
    assert summary["source_5_budget_json"]["status"] == "OK"
    assert summary["lakehouse_exports"]["status"] == "OK"
    assert summary["lakehouse_exports"]["tables"] == ["fixture_dim_titles"]
