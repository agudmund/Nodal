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

        self.setMinimumWidth(Theme.BUTTON_MIN_WIDTH)
        self.setMinimumHeight(Theme.BUTTON_MIN_HEIGHT)

        # Apply our Python-driven styles
        self.update_style()

        font = self.font()
        font.setFamily(Theme.BUTTON_FONT_FAMILY)
        font.setPointSize(Theme.BUTTON_FONT_SIZE)
        font.setBold(Theme.BUTTON_FONT_BOLD)
        self.setFont(font)

    def update_style(self):
        # We use HexArgb to ensure that if we add transparency to the theme later,
        # the stylesheet actually respects the alpha channel.
        base_padding = 5
        top_padding = base_padding + Theme.BUTTON_TEXT_VERTICAL_OFFSET
        bottom_padding = base_padding - Theme.BUTTON_TEXT_VERTICAL_OFFSET
        
        # Clamp to ensure we never have negative padding
        top_padding = max(0, top_padding)
        bottom_padding = max(0, bottom_padding)

        # Theme-driven border logic
        border_width = Theme.BUTTON_BORDER_WIDTH if Theme.BUTTON_BORDER_ENABLED else 0
        
        # Helper for hex conversion
        def to_hex(color): return color.name(QColor.HexArgb)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {to_hex(Theme.BUTTON_BG)};
                border: {border_width}px solid {to_hex(Theme.BUTTON_BORDER)};
                border-radius: 6px;
                color: {to_hex(Theme.TEXT_PRIMARY)};
                padding: {top_padding}px 15px {bottom_padding}px 15px;
            }}
            QPushButton:hover {{
                background-color: {to_hex(Theme.BUTTON_BG_HOVER)};
                border-color: {to_hex(Theme.BUTTON_BORDER_HOVER)};
            }}
            QPushButton:pressed {{
                background-color: {to_hex(Theme.BUTTON_BORDER_HOVER)};
                color: {to_hex(Theme.TEXT_PRIMARY)};
            }}
            QPushButton:disabled {{
                background-color: {to_hex(Theme.BUTTON_BG_INACTIVE)};
                border-color: {to_hex(Theme.BUTTON_BORDER_INACTIVE)};
                color: {to_hex(Theme.BUTTON_BORDER_INACTIVE)};
            }}
        """)