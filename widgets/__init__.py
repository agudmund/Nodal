#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - __init__.py widgets package exports
-Reusable themed widget exports for the application for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt
from graphics.Theme import Theme

class CozyButton(QPushButton):
    """
    A theme-aware button that pulls its 'obsidian' styling 
    directly from our central Theme class.
    """
    def __init__(self, text: str = "Click me", parent=None):
        super().__init__(text, parent)

        self.setMinimumWidth(Theme.buttonMinWidth)
        self.setMinimumHeight(Theme.buttonMinHeight)

        # Apply our Python-driven styles
        self.update_style()

        font = self.font()
        font.setFamily(Theme.buttonFontFamily)
        font.setPointSize(Theme.buttonFontSize)
        font.setBold(Theme.buttonFontBold)
        self.setFont(font)

    def update_style(self):
        # We use HexArgb to ensure that if we add transparency to the theme later,
        # the stylesheet actually respects the alpha channel.
        base_padding = 5
        top_padding = base_padding + Theme.buttonTextVerticalOffset
        bottom_padding = base_padding - Theme.buttonTextVerticalOffset

        # Clamp to ensure we never have negative padding
        top_padding = max(0, top_padding)
        bottom_padding = max(0, bottom_padding)

        # Theme-driven border logic
        border_width = Theme.buttonBorderWidth if Theme.buttonBorderEnabled else 0
        
        # Helper for hex conversion
        def to_hex(color): return color.name(QColor.HexArgb)

        self.setStyleSheet(f"""
           QPushButton {{
               background-color: {to_hex(Theme.buttonBg)};
               border: {border_width}px solid {to_hex(Theme.buttonBorder)};
               border-radius: 6px;
               color: {to_hex(Theme.textPrimary)};
               padding: {top_padding}px 15px {bottom_padding}px 15px;
           }}
           QPushButton:hover {{
               background-color: {to_hex(Theme.buttonBgHover)};
               border-color: {to_hex(Theme.buttonBorderHover)};
           }}
           QPushButton:pressed {{
               background-color: {to_hex(Theme.buttonBorderHover)};
               color: {to_hex(Theme.textPrimary)};
           }}
           QPushButton:disabled {{
               background-color: {to_hex(Theme.buttonBgInactive)};
               border-color: {to_hex(Theme.buttonBorderInactive)};
               color: {to_hex(Theme.buttonBorderInactive)};
            }}
        """)