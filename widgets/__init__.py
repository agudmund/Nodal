#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - widgets custom UI components
-Reusable themed widgets for the application
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt
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
        font.setFamily(Theme.BUTTON_FONT_FAMILY)
        font.setPointSize(Theme.BUTTON_FONT_SIZE)
        font.setBold(Theme.BUTTON_FONT_BOLD)
        self.setFont(font)

    def update_style(self):
        # We use HexArgb for the gradient stop to ensure transparency works
        # Calculate vertical padding - offset top and bottom asymmetrically for text movement
        base_padding = 5
        top_padding = base_padding + Theme.BUTTON_TEXT_VERTICAL_OFFSET
        bottom_padding = base_padding - Theme.BUTTON_TEXT_VERTICAL_OFFSET

        # Ensure padding doesn't go negative
        top_padding = max(0, top_padding)
        bottom_padding = max(0, bottom_padding)

        # Conditionally apply border based on theme setting
        border_width = Theme.BUTTON_BORDER_WIDTH if Theme.BUTTON_BORDER_ENABLED else 0
        border_color = Theme.BUTTON_BORDER.name() if Theme.BUTTON_BORDER_ENABLED else "transparent"
        border_color_hover = Theme.BUTTON_BORDER_HOVER.name() if Theme.BUTTON_BORDER_ENABLED else "transparent"
        border_color_inactive = Theme.BUTTON_BORDER_INACTIVE.name() if Theme.BUTTON_BORDER_ENABLED else "transparent"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BUTTON_BG.name()};
                border: {border_width}px solid {border_color};
                border-radius: 6px;
                color: {Theme.TEXT_PRIMARY.name()};
                padding: {top_padding}px 15px {bottom_padding}px 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BUTTON_BG_HOVER.name()};
                border-color: {border_color_hover};
            }}
            QPushButton:pressed {{
                background-color: {Theme.BUTTON_BG_HOVER.name()};
                color: {Theme.TEXT_PRIMARY.name()};
            }}
            QPushButton:disabled {{
                background-color: {Theme.BUTTON_BG_INACTIVE.name()};
                border-color: {border_color_inactive};
                color: {Theme.get_alpha(Theme.TEXT_PRIMARY, 120).name()};
            }}
        """)