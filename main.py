#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main.py application launcher
-A minor UI for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
import io
import sys
import ctypes
import signal
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from utils.logger import setup_logger
from main_window import NodalApp
from utils.settings import Settings

def log_build_signature(logger, base_path):
    """Reads the Forensic Record and greets the developer with the signature."""
    try:
        version_path = os.path.join(base_path, "resources", "Build Version.md")
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                timestamp = "Unknown"
                signature = "Unknown"
                for line in lines:
                    if "**Timestamp:**" in line:
                        timestamp = line.split("`")[1]
                    if "**Signature:**" in line:
                        signature = line.split("`")[1]
                
                logger.info(f"🧬 Build Signature: [{signature}] | Born: {timestamp}")
        else:
            logger.info("🌱 Running in Dev Mode (No Build Version found)")
    except Exception as e:
        logger.debug(f"Signature handshake skipped: {e}")

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

    # 1. The console handshake, this makes sure that ctrl-c still works
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # 2. Encoding Shield (pythonw-safe)
    if sys.stdout is not None:
        try:
            if sys.stdout.encoding is None or sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            pass

    # 3. The settings injection, we ask the wrapper if High-DPI is enabled before creating the App
    if Settings.is_high_dpi_enabled():
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 4. Initialization
    logger = setup_logger()
    logger.info(f"{APP_NAME} is generally so happy that you are here. ✨")
    
    # This path works for both raw script and PyInstaller EXE
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    log_build_signature(logger, base_path)

    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORG_NAME)

        # 5. Set Application Icon
        icon_path = os.path.join(base_path, "resources", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # 6. Start the Glory
        window = NodalApp()

        geometry = Settings.get_window_geometry()
        if geometry: window.restoreGeometry(geometry)

        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"📍 Starting {APP_NAME} failed catastrophically:\n{str(e)}"
        logger.exception(error_msg, exc_info=True)
        
        if QApplication.instance():
            QMessageBox.critical(None, "Launch Error", error_msg)
        else:
            print(f"\n[!] {error_msg}", file=sys.stderr if sys.stderr else sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()