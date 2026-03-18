#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - log_viewer_tab.py log viewer panel
-Embeddable widget for viewing and filtering application logs, used as the Logs tab in SettingsDialog
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget,
    QTextBrowser, QSlider, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QTimer
from graphics.Theme import Theme


def get_log_file_path():
    cozy_env = os.environ.get("COZYLOG")
    if cozy_env:
        base_path = Path(cozy_env)
    elif hasattr(sys, '_MEIPASS'):
        base_path = Path(sys.executable).parent / "logs"
    else:
        base_path = Path(__file__).resolve().parent.parent / "logs"

    return base_path / "nodal.log"


class LogViewerTab(QWidget):
    """Embeddable log viewer panel — displays and filters application logs.
    Loaded as a tab inside SettingsDialog rather than as a standalone window.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_file = get_log_file_path()

        window_bg    = Theme.windowBg.name()
        text_color   = Theme.textPrimary.name()
        accent_color = Theme.accentNormal.name()

        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }}
            QTextBrowser {{
                background-color: {window_bg};
                color: {text_color};
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
            }}
            QLineEdit {{
                background-color: {Theme.comboboxBg.name()};
                border: 1px solid {accent_color};
                padding: 5px;
                color: {text_color};
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {window_bg};
                color: {text_color};
                border: 1px solid {accent_color};
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.buttonBgHover.name()};
                border: 1px solid {Theme.accentSelected.name()};
            }}
        """)

        main_layout = QHBoxLayout(self)

        # --- Left Side: Content ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        # Path Header
        self.path_label = QLabel(f"📂 SOURCE: {self.log_file}")
        left_layout.addWidget(self.path_label)

        # Search / Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs (e.g., 'ERROR', '✨')...")
        self.search_input.textChanged.connect(self.debounce_filter)
        left_layout.addWidget(self.search_input)

        # Log Display
        self.log_display = QTextBrowser()
        left_layout.addWidget(self.log_display)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_log_content)

        self.explorer_btn = QPushButton("📁 Show in Explorer")
        self.explorer_btn.clicked.connect(self.open_in_explorer)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.explorer_btn)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        # --- Right Side: Cozy vertical scroll slider ---
        self.slider = QSlider(Qt.Vertical)
        self.slider.setStyleSheet("width: 20px;")
        self.slider.valueChanged.connect(self.on_slider_changed)

        main_layout.addWidget(left_container)
        main_layout.addWidget(self.slider)

        # Debounce timer for the search filter
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self._apply_filter_now)

        self.full_content = ""
        self.lines = []
        self.load_log_content()

    def load_log_content(self):
        """Load and display the complete log file content."""
        if not self.log_file.exists():
            self.log_display.setPlainText("Log file not found. ✨ Start the app to generate one.")
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.full_content = f.read()
                self.lines = self.full_content.splitlines()
                self.log_display.setPlainText(self.full_content)
                self.log_display.verticalScrollBar().setValue(
                    self.log_display.verticalScrollBar().maximum()
                )
        except Exception as e:
            self.log_display.setPlainText(f"Error reading log: {e}")

    def open_in_explorer(self):
        """Open the log file location in Windows Explorer."""
        if self.log_file.exists():
            subprocess.run(['explorer', '/select,', str(self.log_file)])

    def debounce_filter(self):
        """Debounce the filter input to avoid excessive filtering on every keystroke."""
        self.filter_timer.start(200)

    def _apply_filter_now(self):
        """Apply the current filter to display matching log lines."""
        search_text = self.search_input.text().strip().lower()
        if not search_text:
            self.log_display.setPlainText(self.full_content)
        else:
            filtered = [l for l in self.lines if search_text in l.lower()]
            self.log_display.setPlainText("\n".join(filtered))

    def on_slider_changed(self, value):
        """Sync the cozy vertical slider to the log display scrollbar."""
        bar = self.log_display.verticalScrollBar()
        bar.setValue(int((value / 100.0) * bar.maximum()))
