#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - main_window.py primary window definition
# A minor UI for enjoying
# Built using a single shared braincell by Yours Truly and some intellectual assistance

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtGui import QIcon


class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Nodal - Note Organizer")
        self.setGeometry(100, 100, 800, 600)

        # Set application icon
        icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add a placeholder button for now
        btn = QPushButton("Create New Note")
        layout.addWidget(btn)

        self.show()
