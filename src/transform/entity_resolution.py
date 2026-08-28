"""Entity resolution engine to match Netflix catalog records with TMDb entities."""

from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from src.transform.cleaner import normalize_title
from src.utils.logger import logger


class EntityResolver:
    """Performs deterministic and fuzzy entity resolution across movie/series catalogs."""

    def __init__(self, match_threshold: float = 85.0) -> None:
        self.match_threshold = match_threshold

    def resolve(
        self,
        netflix_title: str,
        netflix_year: Optional[int],
        candidates: List[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Resolve a Netflix title to the best matching TMDb candidate.

        Returns:
            Tuple of (Best Matching TMDb Candidate or None, Confidence Score 0-100).
        """
        if not candidates:
            return None, 0.0

        norm_target = normalize_title(netflix_title)
        best_candidate: Optional[Dict[str, Any]] = None
        best_score: float = 0.0

        for candidate in candidates:
            cand_title = candidate.get("title") or candidate.get("name") or ""
            norm_cand = normalize_title(cand_title)

            # Calculate string similarity score
            ratio = fuzz.ratio(norm_target, norm_cand)
            token_sort = fuzz.token_sort_ratio(norm_target, norm_cand)
            similarity = max(ratio, token_sort)

            # Year penalty or boost
            cand_date = (
                candidate.get("release_date") or candidate.get("first_air_date") or ""
            )
            cand_year = (
                int(cand_date[:4])
                if len(cand_date) >= 4 and cand_date[:4].isdigit()
                else None
            )

            confidence = similarity
            if netflix_year and cand_year:
                diff = abs(netflix_year - cand_year)
                if diff == 0:
                    confidence = min(100.0, confidence + 5.0)
                elif diff == 1:
                    confidence = min(100.0, confidence)
                elif diff > 2:
                    confidence = max(0.0, confidence - 20.0)

            if confidence > best_score:
                best_score = confidence
                best_candidate = candidate

        if best_score >= self.match_threshold and best_candidate:
            logger.debug(
                f"Resolved '{netflix_title}' ({netflix_year}) -> '{best_candidate.get('title') or best_candidate.get('name')}' (score={best_score:.1f})"
            )
            return best_candidate, best_score

        logger.debug(
            f"No confident match for '{netflix_title}' (best score: {best_score:.1f})"
        )
        return None, best_score
