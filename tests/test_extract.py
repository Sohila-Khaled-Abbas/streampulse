"""Unit tests for extractors."""

from unittest.mock import MagicMock, patch
from src.extract.netflix import NetflixExtractor
from src.extract.tmdb import TMDbExtractor


def test_netflix_extractor_fallback():
    """Test fallback mock dataset when no API key is provided."""
    extractor = NetflixExtractor(api_key=None)
    data = extractor.fetch_recent_additions()
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
            {"id": "nf_999", "title": "Test Film", "type": "movie", "year": 2024}
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
    extractor = TMDbExtractor(api_key=None)
    res = extractor.search_title("Stranger Things")
    assert len(res) >= 1
    assert res[0]["id"] == 66732
