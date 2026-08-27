"""Structured logging setup using loguru."""

import os
import sys

from loguru import logger

from src.utils.config import settings

# Clear default handlers
logger.remove()

def _safe_sink(msg: str) -> None:
    """Safe console sink that encodes to current stdout encoding with error replacement."""
    try:
        sys.stdout.write(msg)
        sys.stdout.flush()
    except UnicodeEncodeError:
        # Fallback to ascii/replace
        enc = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
        clean_bytes = msg.encode(enc, errors="replace")
        sys.stdout.write(clean_bytes.decode(enc, errors="replace"))
        sys.stdout.flush()

# Add safe console handler
logger.add(
    _safe_sink,
    colorize=False,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level.upper(),
)

# Add rotating file handler for persistent logs
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/streampulse_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    encoding="utf-8",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

__all__ = ["logger"]
