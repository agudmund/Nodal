#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - stylesheet.py stylesheet loader
# Loads and applies QSS stylesheets to the application

import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

logger = logging.getLogger("nodal")


def load_stylesheet(app: QApplication) -> bool:
    """
    Load and apply the main stylesheet to the application.

    Args:
        app: QApplication instance

    Returns:
        bool: True if stylesheet loaded successfully, False otherwise
    """
    stylesheet_path = Path(__file__).parent.parent / "resources" / "styles" / "nodal.qss"

    if not stylesheet_path.exists():
        logger.warning(f"Stylesheet not found at {stylesheet_path}")
        return False

    try:
        with open(stylesheet_path, "r", encoding="utf-8") as f:
            stylesheet = f.read()

        app.setStyleSheet(stylesheet)
        logger.info(f"Stylesheet loaded successfully from {stylesheet_path}")
        return True

    except Exception as e:
        logger.error(f"Error loading stylesheet: {e}")
        return False
