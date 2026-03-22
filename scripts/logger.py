"""
Logger Configuration for Google AI Mode Skill
Provides consistent logging across all modules
"""

import logging
import sys
from pathlib import Path
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    """
    Set up a logger with consistent formatting

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional file path to write logs
        format_string: Log format string
        date_format: Date format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(format_string, datefmt=date_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default settings

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
