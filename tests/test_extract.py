"""Unit tests for extractors and TMDb resolution."""

from unittest.mock import MagicMock, patch
from src.extract.netflix import NetflixExtractor
from src.extract.netflix_scraper import NetflixWebScraper
from src.extract.tmdb import TMDbExtractor
from src.extract.enricher_scraper import WebEnricher
from src.extract.historical_loader import HistoricalDatasetLoader


def test_netflix_extractor_fallback():
    """Test fallback mock dataset when no API key is provided."""
    extractor = NetflixExtractor(api_key="")
    data = extractor._get_mock_catalog_data()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "title" in data[0]
    assert "id" in data[0]


@patch("src.extract.netflix.requests.get")
def test_netflix_extractor_api(mock_get):
    """Test API parsing when API key is set."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "results": [
            {"id": "nf_999", "title": "Test Film", "type": "movie", "year": 2026}
        ]
    }
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    extractor = NetflixExtractor(api_key="valid_key", host="unogsng.p.rapidapi.com")
    data = extractor.fetch_recent_additions(days_back=5, limit=10)
    assert len(data) == 1
    assert data[0]["title"] == "Test Film"


def test_tmdb_extractor_mock_search():
    """Test TMDb search with offline mock fallback."""
    extractor = TMDbExtractor(api_key="")
    res = extractor._get_mock_tmdb_search("Stranger Things", 2016)
    assert len(res) >= 1
    assert res[0]["id"] == 66732


def test_netflix_web_scraper_fallback():
    """Test Netflix web scraper fallback mechanism."""
    scraper = NetflixWebScraper()
    data = scraper._get_fallback_catalog()
    assert len(data) >= 3
    assert data[0]["title"] == "People We Meet on Vacation"
    assert data[0]["release_year"] == 2026
    assert data[0]["id"].startswith("wiki_2026_")


def test_historical_dataset_loader():
    """Test historical dataset loader safe parsers."""
    assert HistoricalDatasetLoader._safe_float("8.5") == 8.5
    assert HistoricalDatasetLoader._safe_float(None) is None
    assert HistoricalDatasetLoader._safe_int("120") == 120
    assert HistoricalDatasetLoader._safe_int("") is None


def test_web_enricher_deterministic_metrics():
    """Test WebEnricher produces valid rating and popularity metrics."""
    enricher = WebEnricher()
    sample = {
        "netflix_id": "test_001",
        "title": "People We Meet on Vacation",
        "release_year": 2026,
        "media_type": "movie",
        "date_added": "2026-01-09",
    }
    enriched = enricher.enrich_title(sample)
    assert enriched["vote_average"] >= 6.0
    assert enriched["vote_count"] > 0
    assert enriched["popularity"] > 0
    assert enriched["days_to_streaming"] == 9
