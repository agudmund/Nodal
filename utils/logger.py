#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - logger.py logging configuration
-Sets up file and console logging for the application
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logger(name: str = "nodal") -> logging.Logger:
    """
    Configure and return a logger that writes to both console and file.
    Log files rotate daily at midnight and append to the same day's log.

    Args:
        name: Logger name (default: "nodal")

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if handlers don't already exist (avoid duplicates)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Log file path (same file name, rotates daily)
    log_file = logs_dir / "nodal.log"

    # Formatter for consistent output
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Timed rotating file handler (rotates daily at midnight)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y%m%d"  # Add date suffix to rotated files
    logger.addHandler(file_handler)

    # Console handler (writes to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized - Log file: {log_file}")

    return logger
