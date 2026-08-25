"""Structured logging setup using loguru."""

import sys
from loguru import logger
from src.utils.config import settings

# Clear default handlers
logger.remove()

# Add standard console handler with colored formatting
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper(),
)

# Add rotating file handler for persistent logs
logger.add(
    "logs/streampulse_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

__all__ = ["logger"]
