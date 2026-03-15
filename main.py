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
import ctypes
import signal
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from utils.logger import setup_logger
from main_window import NodalApp
from utils.settings import Settings

# --- Windows Taskbar Icon Fix ---
try:
    # Forces Windows to treat the EXE as a unique application with its own icon
    myappid = 'SingleSharedBraincell.Nodal.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

APP_NAME = "Nodal"
ORG_NAME = "Single Shared Braincell"

def main():

    # 1. THE TERMINAL HANDSHAKE
    # Tell the OS to let Ctrl-C terminate the Python process immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # 1. Encoding Shield (pythonw-safe)
    if sys.stdout is not None:
        try:
            if sys.stdout.encoding is None or sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            pass

    # 2. THE SETTINGS INJECTION (Step 3)
    # We ask the wrapper if High-DPI is enabled before creating the App
    if Settings.is_high_dpi_enabled():
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

        # 4. Set Application Icon
        # This path works for both raw script and PyInstaller EXE
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "resources", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # 5. Launch the Vessel
        window = NodalApp()

        geometry = Settings.get_window_geometry()
        if geometry: window.restoreGeometry(geometry)

        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"Starting {APP_NAME} failed catastrophically:\n{str(e)}"
        logger.exception(error_msg, exc_info=True)
        
        if QApplication.instance():
            QMessageBox.critical(None, "Launch Error", error_msg)
        else:
            print(f"\n[!] {error_msg}", file=sys.stderr if sys.stderr else sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()