"""Logging configuration for ResearchGuard.
Ensures rotating file logs without leaking sensitive document content.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from app.config import LOG_FILE_PATH

_logger_initialized = False


def setup_logger(name: str = "ResearchGuard") -> logging.Logger:
    """Configures and returns the application logger."""
    global _logger_initialized
    logger = logging.getLogger(name)

    if not _logger_initialized:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Rotating file handler: 5MB per file, up to 5 backups
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not configure file logger: {e}", file=sys.stderr)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        _logger_initialized = True

    return logger


logger = setup_logger()
