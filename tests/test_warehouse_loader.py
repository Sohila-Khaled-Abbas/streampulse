"""Unit tests for warehouse loader and file exports."""

import os
from src.load.warehouse_loader import WarehouseLoader


def test_warehouse_loader_file_export(tmp_path):
    """Test warehouse loader file export mechanism."""
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
