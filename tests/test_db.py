"""Unit tests for database manager and configuration."""

from src.utils.config import Settings
from src.utils.db import DatabaseManager


def test_settings_url():
    """Verify generated database URL."""
    custom_settings = Settings(
        db_user="testuser",
        db_password="secretpassword",
        db_host="127.0.0.1",
        db_port=5433,
        db_name="testdb",
    )
    assert (
        custom_settings.database_url
        == "postgresql://testuser:secretpassword@127.0.0.1:5433/testdb?sslmode=prefer"
    )


def test_settings_url_encodes_credentials_and_accepts_required_ssl():
    """Ensure reserved credential characters are URL-encoded and SSL mode is configurable."""
    custom_settings = Settings(
        db_user="user@example",
        db_password="p@ss/word?x",
        db_host="db.example.test",
        db_name="streampulse",
        db_sslmode="require",
    )

    assert custom_settings.database_url == (
        "postgresql://user%40example:p%40ss%2Fword%3Fx"
        "@db.example.test:5432/streampulse?sslmode=require"
    )


def test_db_manager_offline():
    """Verify test_connection returns false gracefully on invalid connection."""
    mgr = DatabaseManager(database_url="postgresql://fake:fake@127.0.0.1:59999/fake")
    assert mgr.test_connection() is False
