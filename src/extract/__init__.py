"""Extractors for third-party streaming and movie metadata APIs."""

from src.extract.netflix import NetflixExtractor
from src.extract.tmdb import TMDbExtractor

__all__ = ["NetflixExtractor", "TMDbExtractor"]
