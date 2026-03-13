#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - logger.py logging configuration
-Sets up file and console logging for the application
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import sys
import logging
import logging.handlers
from pathlib import Path

def setup_logger(name: str = "nodal") -> logging.Logger:
    """
    Configure and return a logger that writes to both console and file.
    Log files rotate daily at midnight and append to the same day's log.
    """
    logger = logging.getLogger(name)

    # Only configure if handlers don't already exist (avoid duplicates)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # 1. Setup Paths
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "nodal.log"

    # 2. Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Stream Handler (Console)
    # We explicitly set the stream and terminator to handle Windows encoding better
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    # 4. File Handler (Rotating)
    # This is the 'One True' file handler for the app
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8' # Ensures the Sparkle ✨ is saved correctly to disk
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = "%Y%m%d"

    # 5. Add Handlers to Logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger