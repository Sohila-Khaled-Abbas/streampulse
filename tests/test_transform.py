"""Unit tests for title normalization, cleaning, and fuzzy entity resolution."""

from src.transform.cleaner import clean_title_record, normalize_title
from src.transform.entity_resolution import EntityResolver


def test_normalize_title():
    """Test standardizing title text."""
    assert normalize_title("The Godfather: Part II") == "the godfather part 2"
    assert (
        normalize_title("Spider-Man: No Way Home (2021)")
        == "spider man no way home 2021"
    )
    assert normalize_title("  Stranger   Things! ") == "stranger things"


def test_clean_title_record():
    """Test cleaning raw dictionary payload."""
    raw = {
        "id": "12345",
        "title": " Glass Onion: A Knives Out Mystery ",
        "type": "movie",
        "runtime": 8340,
        "year": "2022",
        "rating": "PG-13",
    }
    cleaned = clean_title_record(raw)
    assert cleaned["netflix_id"] == "12345"
    assert cleaned["title"] == "Glass Onion: A Knives Out Mystery"
    assert cleaned["release_year"] == 2022
    assert cleaned["runtime_minutes"] == 139
    assert cleaned["media_type"] == "movie"


def test_entity_resolver_exact_match():
    """Test high-confidence exact match."""
    resolver = EntityResolver(match_threshold=80.0)
    candidates = [
        {"id": 66732, "name": "Stranger Things", "first_air_date": "2016-07-15"}
    ]
    match, score = resolver.resolve(
        netflix_title="Stranger Things",
        netflix_year=2016,
        candidates=candidates,
    )
    assert match is not None
    assert match["id"] == 66732
    assert score >= 90.0


def test_entity_resolver_no_match():
    """Test filtering out irrelevant candidates."""
    resolver = EntityResolver(match_threshold=85.0)
    candidates = [
        {
            "id": 999,
            "name": "Completely Unrelated Movie",
            "first_air_date": "1990-01-01",
        }
    ]
    match, score = resolver.resolve(
        netflix_title="Stranger Things",
        netflix_year=2016,
        candidates=candidates,
    )
    assert match is None
    assert score < 50.0
