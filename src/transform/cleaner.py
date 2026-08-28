"""Data cleaning and normalization utilities for streaming catalog records."""

import re
from typing import Any, Dict


def normalize_title(title: str) -> str:
    """Normalize title for matching by stripping symbols, extra whitespace, and standardizing casing."""
    if not title:
        return ""
    text = title.lower()
    # Replace Roman numerals in common sequels
    text = re.sub(r"\bpart\s+ii\b", "part 2", text)
    text = re.sub(r"\bpart\s+iii\b", "part 3", text)
    text = re.sub(r"\bpart\s+iv\b", "part 4", text)
    # Remove punctuation & special characters
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    return " ".join(text.split())


def clean_title_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and standardize raw Netflix API catalog dictionary."""
    runtime = raw.get("runtime")
    runtime_mins = None
    if isinstance(runtime, (int, float)) and runtime > 0:
        # Convert seconds to minutes if value is large, otherwise retain minutes
        runtime_mins = int(runtime // 60) if runtime > 500 else int(runtime)

    year = raw.get("year") or raw.get("release_year")
    try:
        year_int = int(year) if year is not None else None
    except (ValueError, TypeError):
        year_int = None

    return {
        "netflix_id": str(raw.get("id") or raw.get("netflix_id")),
        "title": str(raw.get("title", "")).strip(),
        "normalized_title": normalize_title(str(raw.get("title", ""))),
        "media_type": (
            "series"
            if str(raw.get("type", "")).lower() in ("series", "tv", "show")
            else "movie"
        ),
        "synopsis": raw.get("synopsis") or raw.get("overview") or "",
        "release_year": year_int,
        "runtime_minutes": runtime_mins,
        "maturity_rating": raw.get("maturity_rating") or raw.get("rating") or "Unrated",
        "date_added": raw.get("date_added"),
    }
