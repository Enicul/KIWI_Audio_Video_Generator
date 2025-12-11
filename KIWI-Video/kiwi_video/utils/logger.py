"""Logging configuration for KIWI-Video."""

import logging
import sys
from pathlib import Path

from loguru import logger

from kiwi_video.utils.config import settings


def setup_logging(log_file: Path | None = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_file: Optional path to log file
    """
    # Remove default handler
    logger.remove()

    # Console handler with colored output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # File handler if specified
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    # Bind the name to loguru logger
    return logger.bind(name=name)


# Setup logging on module import
setup_logging()

