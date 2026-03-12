#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - widgets custom UI components
-Reusable themed widgets for the application
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont, QColor
from utils.theme import Theme

class CozyButton(QPushButton):
    """
    A theme-aware button that pulls its 'obsidian' styling 
    directly from our central Theme class.
    """
    def __init__(self, text: str = "Click me", parent=None):
        super().__init__(text, parent)

        self.setMinimumWidth(100)
        self.setMinimumHeight(36)

        # Apply our Python-driven styles
        self.update_style()

        font = self.font()
        font.setFamily("Lato")
        font.setPointSize(11)
        font.setBold(True)
        self.setFont(font)

    def update_style(self):
        # We use HexArgb for the gradient stop to ensure transparency works
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {Theme.get_alpha(Theme.ACCENT_NORMAL, 100).name(QColor.HexArgb)}, 
                            stop:1 {Theme.TOOLBAR_BG.name()});
                border: 1px solid {Theme.TOOLBAR_BORDER.name()};
                border-radius: 6px;
                color: {Theme.TEXT_PRIMARY.name()};
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background: {Theme.get_alpha(Theme.ACCENT_SELECTED, 60).name(QColor.HexArgb)};
                border-color: {Theme.ACCENT_SELECTED.name()};
            }}
            QPushButton:pressed {{
                background: {Theme.ACCENT_SELECTED.name()};
                color: #000000;
            }}
        """)