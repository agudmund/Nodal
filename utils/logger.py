#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - logger.py logging configuration
# Sets up file and console logging for the application

import logging
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "nodal") -> logging.Logger:
    """
    Configure and return a logger that writes to both console and file.

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

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"nodal_{timestamp}.log"

    # Formatter for consistent output
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler (writes to file)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (writes to console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized - Log file: {log_file}")

    return logger
