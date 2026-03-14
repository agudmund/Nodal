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
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from utils.logger import setup_logger
from main_window import NodalApp

APP_NAME = "Nodal"
ORG_NAME = "Single Shared Braincell"

def main():
    # 1. Encoding Shield (pythonw-safe)
    # We check if stdout exists before touching it to avoid NoneType errors
    if sys.stdout is not None:
        try:
            if sys.stdout.encoding is None or sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            pass

    if sys.stderr is not None:
        try:
            if sys.stderr.encoding is None or sys.stderr.encoding.lower() != 'utf-8':
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            pass

    # 2. High-DPI Precision (Modern Qt6 Style)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 3. Initialization
    # Initialize the logger early so we can capture as much as possible
    logger = setup_logger()
    logger.info(f"{APP_NAME} is generally so happy that you are here. ✨")

    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORG_NAME)

        logger.debug("QApplication created successfully")

        # 4. Launch the Obsidian Vessel
        window = NodalApp()
        # Ensure the window is actually shown!
        window.show() 

        sys.exit(app.exec())

    except Exception as e:
        # Log the error professionally
        error_msg = f"Starting {APP_NAME} failed catastrophically:\n{str(e)}"
        try:
            logger.exception(error_msg, exc_info=True)
        except:
            pass

        # 5. The Visual Safety Net
        # If we are in pythonw, we need a GUI popup to show the error
        if QApplication.instance():
            QMessageBox.critical(None, "Launch Error", error_msg)
        else:
            # Fallback to console if GUI hasn't started
            print(f"\n[!] {error_msg}", file=sys.stderr if sys.stderr else sys.stdout)
        
        sys.exit(1)

if __name__ == "__main__":
    main()