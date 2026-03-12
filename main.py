#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main.py application launcher
-A minor UI for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import sys
from PySide6.QtWidgets import QApplication
from utils.logger import setup_logger
from main_window import NodalApp


def main():
    # Initialize logger first
    logger = setup_logger()
    logger.info("Starting Nodal Application")

    try:
        app = QApplication(sys.argv)
        logger.debug("QApplication created successfully")

        window = NodalApp()
        logger.info("Main window initialized and displayed")

        sys.exit(app.exec())
    except Exception as e:
        logger.exception("Fatal error in application startup", exc_info=True)
        raise


if __name__ == "__main__":
    main()
