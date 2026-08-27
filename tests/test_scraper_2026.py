"""Unit tests for 2026 web scraper and data profiler."""

from src.extract.netflix_scraper import NetflixWebScraper
from src.transform.profiler import DataProfiler


def test_netflix_web_scraper_parsers():
    """Test runtime and date parsing logic."""
    scraper = NetflixWebScraper()

    # Runtimes
    assert scraper._parse_runtime("1 h 57 min") == 117
    assert scraper._parse_runtime("2 h") == 120
    assert scraper._parse_runtime("45 min") == 45
    assert scraper._parse_runtime("118 minutes") == 118
    assert scraper._parse_runtime("") is None

    # Dates
    assert scraper._format_date("January 9, 2026", 2026) == "2026-01-09"
    assert scraper._format_date("February 20, 2026", 2026) == "2026-02-20"
    assert scraper._format_date("Late 2026", 2026) == "2026-11-15"
    assert scraper._format_date("Mid-2026", 2026) == "2026-06-15"


def test_data_profiler_statistics():
    """Test DataProfiler generates valid quality report."""
    profiler = DataProfiler()
    sample_records = [
        {
            "netflix_id": "wiki_2026_01",
            "title": "People We Meet on Vacation",
            "media_type": "movie",
            "release_year": 2026,
            "runtime_minutes": 118,
            "maturity_rating": "PG-13",
            "vote_average": 7.8,
            "vote_count": 2500,
            "popularity": 120.5,
            "match_confidence": 95.0,
            "date_added": "2026-01-09",
            "source": "wikipedia_2026_films",
        },
        {
            "netflix_id": "wiki_2026_02",
            "title": "Stranger Things 5",
            "media_type": "series",
            "release_year": 2026,
            "runtime_minutes": 65,
            "maturity_rating": "TV-14",
            "vote_average": 8.9,
            "vote_count": 45000,
            "popularity": 320.0,
            "match_confidence": 100.0,
            "date_added": "2026-05-20",
            "source": "wikipedia_tv_series",
        }
    ]

    report = profiler.profile_dataset(sample_records)
    assert report["validation_status"] == "PASSED"
    assert report["quality_score"] >= 90.0
    assert report["total_records"] == 2
    assert report["era_breakdown"]["2026_live"] == 2
    assert report["media_type_breakdown"]["movie"] == 1
    assert report["media_type_breakdown"]["series"] == 1
    assert report["metrics"]["average_rating"] == 8.35
