#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - demo_dialog.py proof of concept
-Simple example dialog demonstrating CozyDialog base class reusability
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from utils.theme import Theme
from widgets.cozy_dialog import CozyDialog
from widgets import CozyButton


class DemoDialog(CozyDialog):
    """Proof of concept dialog showing CozyDialog reusability."""

    def __init__(self, parent=None):
        super().__init__(title="This window is a bit extra 🌿", parent=parent)
        self.setFixedSize(500, 300)

    def _setup_content(self):
        """Create a simple content area."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("It's a happy little extra window ✨")
        label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY.name()};
            font-size: 16px;
            font-weight: bold;
        """)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        layout.addStretch()

        return container

    def _setup_bottom_buttons(self, layout):
        """Add Close button to dialog bottom bar."""
        close_btn = CozyButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
