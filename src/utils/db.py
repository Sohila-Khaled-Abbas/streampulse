"""Database connection manager and session helper for PostgreSQL."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from src.utils.config import settings
from src.utils.logger import logger


class DatabaseManager:
    """Manages PostgreSQL engine creation and connection lifecycles."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or settings.database_url
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        """Lazy initialization of SQLAlchemy engine with connection pool."""
        if self._engine is None:
            logger.info("Initializing PostgreSQL SQLAlchemy connection pool...")
            self._engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
            )
        return self._engine

    @contextmanager
    def connect(self) -> Generator[Connection, None, None]:
        """Context manager yielding a transactional database connection."""
        conn = self.engine.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            conn.close()

    def test_connection(self) -> bool:
        """Verify connectivity to the database instance."""
        try:
            with self.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                logger.info(f"Database connection verified successfully (result={result}).")
                return result == 1
        except Exception as err:
            logger.warning(f"Database connection test failed: {err}")
            return False


db_manager = DatabaseManager()
