"""Logging configuration for the BRS backend."""

import logging
from brs_backend.core.config import settings


def setup_logging():
    """Configure logging based on environment settings."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Level: {settings.LOG_LEVEL}, Detailed: {settings.ENABLE_DETAILED_LOGGING}"
    )

    return logger


def log_detailed(message, level="info"):
    """Log detailed messages only if detailed logging is enabled."""
    if settings.ENABLE_DETAILED_LOGGING:
        logger = logging.getLogger(__name__)
        getattr(logger, level)(message)


# Set up logging
logger = setup_logging()
