#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main.py application launcher
-A minor UI for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import sys
import os
import io
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from utils.logger import setup_logger
from main_window import NodalApp

APP_NAME = "Nodal"
ORG_NAME = "Single Shared Braincell"

def main():
    # 1. Encoding Shield
    # Force UTF-8 for terminal output so ✨ and other cozy characters 
    # don't trigger the 'cp1252' charmap error on Windows terminals.
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 2. High-DPI Precision (Modern Qt6 Style)
    # This prevents the 'Gaussian Tax' performance hit we saw earlier
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 3. Initialization
    logger = setup_logger()
    logger.info(f"{APP_NAME} is generally so happy that you are here. ✨")

    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORG_NAME)

        logger.debug("QApplication created successfully")

        # 4. Launch the Obsidian Vessel
        window = NodalApp()

        sys.exit(app.exec())
    except Exception as e:
        # 1. Attempt the professional way
        try:
            logger.exception(f"Starting {APP_NAME} failed catastrophically.", exc_info=True)
        except Exception:
            # If the logger itself is broken, we don't want to crash during the crash!
            pass

        # 2. The Brute Force Safety Net (Your 'Void' Print)
        # We use stderr to ensure it pops up even if stdout is being piped elsewhere
        print(f"\n[!] {APP_NAME} has entered the void: {str(e)}", file=sys.stderr)
        
        # 3. Clean Exit
        # sys.exit(1) is the proper way to tell the OS 'Something went wrong'
        sys.exit(1)

if __name__ == "__main__":
    main()
