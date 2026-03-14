#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - logger.py its really just a fancypants print statement wrapper
-A logger for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path

def get_base_dir() -> Path:
    """
    Returns the absolute path to the directory containing the executable or script.
    Works for standard Python execution and PyInstaller bundles.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller EXE
        return Path(sys.executable).parent
    # Running as a normal script
    return Path(__file__).resolve().parent.parent

def setup_logger(name: str = "nodal") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # 1. Setup Paths with Environment Variable Priority
    # Check for $COZYLOG first. If it's not set, use the smart fallback.
    cozy_env = os.environ.get("COZYLOG")
    
    if cozy_env:
        logs_dir = Path(cozy_env)
    else:
        logs_dir = get_base_dir() / "logs"

    try:
        logs_dir.mkdir(exist_ok=True, parents=True)
    except Exception:
        # Emergency fallback if the chosen directory isn't writable
        logs_dir = Path(os.path.expanduser("~")) / ".nodal_logs"
        logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "nodal.log"

    # 2. Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Stream Handler (Console)
    # We check if sys.stdout exists (safety for pythonw)
    if sys.stdout is not None:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

    # 4. File Handler (Rotating)
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

    # 5. Add Handler to Logger
    logger.addHandler(file_handler)

    return logger