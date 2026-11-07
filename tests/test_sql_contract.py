"""Contract checks between PostgreSQL DDL and the Python warehouse loader."""

import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORTING_SQL = (ROOT / "sql" / "02_reporting.sql").read_text(encoding="utf-8")
LOADER_SOURCE = (ROOT / "src" / "load" / "warehouse_loader.py").read_text(
    encoding="utf-8"
)


def test_talent_loader_targets_schema_tables():
    assert "CREATE TABLE IF NOT EXISTS reporting.dim_talent_crew" in REPORTING_SQL
    assert "CREATE TABLE IF NOT EXISTS reporting.bridge_title_talent" in REPORTING_SQL
    assert "INSERT INTO reporting.dim_talent_crew" in LOADER_SOURCE
    assert "INSERT INTO reporting.bridge_title_talent" in LOADER_SOURCE
    assert "reporting.dim_crew" not in LOADER_SOURCE
    assert "reporting.bridge_title_crew" not in LOADER_SOURCE


def test_performance_insert_columns_exist_in_reporting_schema():
    match = re.search(
        r"INSERT INTO reporting\.fact_streaming_performance\s*\((.*?)\)\s*VALUES",
        LOADER_SOURCE,
        re.DOTALL,
    )
    assert match is not None
    insert_columns = [column.strip() for column in match.group(1).split(",")]

    for column in insert_columns:
        assert re.search(rf"\b{re.escape(column)}\b", REPORTING_SQL), column


def test_initialization_has_no_provider_specific_postgres_role_grant():
    init_sql = (ROOT / "sql" / "00_init.sql").read_text(encoding="utf-8")
    assert "TO postgres" not in init_sql
