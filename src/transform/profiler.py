"""Data Quality Validation and Catalog Profiling Engine for StreamPulse."""

import json
import os
from typing import Any, Dict, List

from src.utils.logger import logger


class DataProfiler:
    """Performs statistical profiling, completeness checks, and data quality validation."""

    def __init__(self, output_dir: str = os.path.join("data", "processed")) -> None:
        self.output_dir = output_dir

    def profile_dataset(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistical profile and validation report for records.

        Args:
            records: List of cleaned, enriched catalog dictionaries.

        Returns:
            Dictionary containing metrics, distributions, quality score, and validation status.
        """
        total_count = len(records)
        if total_count == 0:
            logger.warning("DataProfiler received 0 records to profile.")
            return {"status": "EMPTY", "total_records": 0}

        # 1. Null / Completeness Audit
        field_stats: Dict[str, Dict[str, Any]] = {}
        target_fields = [
            "netflix_id",
            "title",
            "media_type",
            "release_year",
            "runtime_minutes",
            "maturity_rating",
            "vote_average",
            "vote_count",
            "popularity",
            "match_confidence",
            "date_added",
            "source",
        ]

        for field in target_fields:
            non_null_count = sum(
                1
                for r in records
                if r.get(field) is not None and str(r.get(field)).strip() != ""
            )
            completeness_pct = round((non_null_count / total_count) * 100, 2)
            field_stats[field] = {
                "present_count": non_null_count,
                "missing_count": total_count - non_null_count,
                "completeness_pct": completeness_pct,
            }

        # 2. Release Era Breakdown
        era_counts = {"2026_live": 0, "2024_2025_modern": 0, "historical_archive": 0}
        type_counts = {"movie": 0, "series": 0}
        ratings_tiers = {"top_rated": 0, "good": 0, "mixed": 0, "unrated": 0}
        match_confidence_tiers = {
            "high_confidence_ge_90": 0,
            "medium_confidence_75_89": 0,
            "low_confidence_lt_75": 0,
        }

        ratings_list: List[float] = []
        popularity_list: List[float] = []
        runtime_list: List[int] = []
        genre_freq: Dict[str, int] = {}

        for r in records:
            # Era
            year = r.get("release_year") or r.get("year") or 0
            if year == 2026:
                era_counts["2026_live"] += 1
            elif year in (2024, 2025):
                era_counts["2024_2025_modern"] += 1
            else:
                era_counts["historical_archive"] += 1

            # Media Type
            m_type = str(r.get("media_type", "movie")).lower()
            type_counts[m_type] = type_counts.get(m_type, 0) + 1

            # Rating
            vote_avg = r.get("vote_average")
            if (
                vote_avg is not None
                and isinstance(vote_avg, (int, float))
                and vote_avg > 0
            ):
                ratings_list.append(float(vote_avg))
                if vote_avg >= 8.0:
                    ratings_tiers["top_rated"] += 1
                elif vote_avg >= 6.5:
                    ratings_tiers["good"] += 1
                else:
                    ratings_tiers["mixed"] += 1
            else:
                ratings_tiers["unrated"] += 1

            # Popularity
            pop = r.get("popularity")
            if pop is not None and isinstance(pop, (int, float)):
                popularity_list.append(float(pop))

            # Runtime
            rt = r.get("runtime_minutes")
            if rt is not None and isinstance(rt, (int, float)) and rt > 0:
                runtime_list.append(int(rt))

            # Match Confidence
            conf = r.get("match_confidence", 100.0)
            if conf >= 90.0:
                match_confidence_tiers["high_confidence_ge_90"] += 1
            elif conf >= 75.0:
                match_confidence_tiers["medium_confidence_75_89"] += 1
            else:
                match_confidence_tiers["low_confidence_lt_75"] += 1

            # Genres
            genres = r.get("genre") or r.get("genres") or "Unknown"
            if isinstance(genres, list):
                for g in genres:
                    g_clean = str(g).strip().title()
                    genre_freq[g_clean] = genre_freq.get(g_clean, 0) + 1
            elif isinstance(genres, str):
                for g in genres.split("/"):
                    g_clean = g.strip().title()
                    if g_clean:
                        genre_freq[g_clean] = genre_freq.get(g_clean, 0) + 1

        avg_rating = (
            round(sum(ratings_list) / len(ratings_list), 2) if ratings_list else 0.0
        )
        avg_pop = (
            round(sum(popularity_list) / len(popularity_list), 2)
            if popularity_list
            else 0.0
        )
        avg_runtime = (
            round(sum(runtime_list) / len(runtime_list), 1) if runtime_list else 0.0
        )

        top_genres = dict(
            sorted(genre_freq.items(), key=lambda item: item[1], reverse=True)[:8]
        )

        # 3. Overall Data Quality Score (0 - 100)
        title_completeness = field_stats.get("title", {}).get("completeness_pct", 100.0)
        id_completeness = field_stats.get("netflix_id", {}).get(
            "completeness_pct", 100.0
        )
        year_completeness = field_stats.get("release_year", {}).get(
            "completeness_pct", 100.0
        )
        rating_completeness = field_stats.get("vote_average", {}).get(
            "completeness_pct", 100.0
        )

        quality_score = round(
            (title_completeness * 0.35)
            + (id_completeness * 0.25)
            + (year_completeness * 0.20)
            + (rating_completeness * 0.20),
            1,
        )

        validation_passed = bool(quality_score >= 85.0 and total_count > 0)

        report = {
            "validation_status": "PASSED" if validation_passed else "WARNING",
            "quality_score": quality_score,
            "total_records": total_count,
            "era_breakdown": era_counts,
            "media_type_breakdown": type_counts,
            "rating_tier_distribution": ratings_tiers,
            "match_confidence_distribution": match_confidence_tiers,
            "metrics": {
                "average_rating": avg_rating,
                "average_popularity": avg_pop,
                "average_runtime_minutes": avg_runtime,
            },
            "top_genres": top_genres,
            "field_completeness": field_stats,
        }

        # 4. Save JSON Report
        os.makedirs(self.output_dir, exist_ok=True)
        report_file = os.path.join(self.output_dir, "data_profiling_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self._print_console_summary(report)
        return report

    def _print_console_summary(self, report: Dict[str, Any]) -> None:
        """Prints a clean ASCII data profiling dashboard in the terminal logs."""
        logger.info(
            "================================================================================"
        )
        logger.info("[REPORT] STREAMPULSE DATA QUALITY & CATALOG PROFILING REPORT")
        logger.info(
            "================================================================================"
        )
        logger.info(
            f"Validation Status: [{report['validation_status']}] | "
            f"Quality Score: {report['quality_score']}% | "
            f"Total Processed: {report['total_records']:,} titles"
        )
        logger.info(
            "--------------------------------------------------------------------------------"
        )
        logger.info(
            f"Catalog Eras: 2026 Live: {report['era_breakdown']['2026_live']:,} | "
            f"2024-2025 Modern: {report['era_breakdown']['2024_2025_modern']:,} | "
            f"Historical Archive: {report['era_breakdown']['historical_archive']:,}"
        )
        logger.info(
            f"Media Distribution: Movies: {report['media_type_breakdown'].get('movie', 0):,} | "
            f"Series/Shows: {report['media_type_breakdown'].get('series', 0):,}"
        )
        logger.info(
            f"Audience Metrics: Mean Rating: {report['metrics']['average_rating']} / 10 | "
            f"Mean Popularity: {report['metrics']['average_popularity']} | "
            f"Mean Runtime: {report['metrics']['average_runtime_minutes']} mins"
        )
        logger.info(
            f"Entity Resolution: High Conf (>=90%): {report['match_confidence_distribution']['high_confidence_ge_90']:,} | "
            f"Medium (75-89%): {report['match_confidence_distribution']['medium_confidence_75_89']:,}"
        )
        logger.info(
            f"Top Genres: {', '.join([f'{k} ({v})' for k, v in list(report['top_genres'].items())[:5]])}"
        )
        logger.info(
            "================================================================================"
        )


data_profiler = DataProfiler()
