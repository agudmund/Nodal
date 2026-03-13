#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - theme.py color and styling system
-Centralized theme management for consistent UI appearance
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtGui import QColor

class Theme:
    # --- Sizing & Spacing ---
    BORDER_WIDTH = 2  # Border width in pixels (toolbar and canvas edges)
    
    # --- Button Styling ---
    BUTTON_FONT_FAMILY = "Segoe UI"
    BUTTON_FONT_SIZE = 10  # Point size
    BUTTON_FONT_BOLD = False
    BUTTON_TEXT_VERTICAL_OFFSET = -2  # Vertical offset in pixels (positive = down, negative = up)
    BUTTON_BORDER_WIDTH = 2  # Border width for all UI buttons
    BUTTON_BORDER_ENABLED = True  # Toggle to show/hide button borders

    # --- Button Colors ---
    BUTTON_BG = QColor("#3a3a3a")
    BUTTON_BORDER = QColor("#1e1e1e")
    BUTTON_BG_HOVER = QColor("#1e1e1e")
    BUTTON_BORDER_HOVER = QColor("#6b5a47")
    BUTTON_BG_INACTIVE = QColor("#1f1f1f")
    BUTTON_BORDER_INACTIVE = QColor("#4a4a4a")

    # --- Primary Branding ---
    ACCENT_NORMAL = QColor("#3498db")
    ACCENT_SELECTED = QColor("#00d2ff")
    TEXT_PRIMARY = QColor("#ffffff")
    
    # --- Window & Toolbar ---
    WINDOW_BG = QColor("#1e1e1e")
    TOOLBAR_BG = QColor("#1e1e1e")
    TOOLBAR_BORDER = QColor("#6b5a47")
    
    # --- Scene Background ---
    FROST_COLOR = QColor(30, 30, 35, 150)
    GRID_COLOR = QColor(200, 200, 200, 30)

    # --- Node Specifics ---
    NODE_GRADIENT_TOP = QColor(55, 55, 60, 255)    # Solid Slate
    NODE_GRADIENT_BOTTOM = QColor(25, 25, 30, 255) # Solid Obsidian
    NODE_BORDER_NORMAL = QColor(255, 255, 255, 40) # Subtle white rim light
    
    @staticmethod
    def get_alpha(color: QColor, alpha: int):
        """Helper to quickly swap alpha without hardcoding RGB elsewhere."""
        return QColor(color.red(), color.green(), color.blue(), alpha)

    @staticmethod
    def adjust_brightness(color: QColor, factor: float):
        """
        factor > 1.0 makes it brighter, < 1.0 makes it darker.
        Example: Theme.adjust_brightness(Theme.ACCENT_NORMAL, 0.8) # 20% darker
        """
        r = max(0, min(255, int(color.red() * factor)))
        g = max(0, min(255, int(color.green() * factor)))
        b = max(0, min(255, int(color.blue() * factor)))
        return QColor(r, g, b, color.alpha())

    @staticmethod
    def lerp(color1: QColor, color2: QColor, t: float):
        """Linearly interpolates between two colors (t from 0.0 to 1.0)"""
        r = int(color1.red() + (color2.red() - color1.red()) * t)
        g = int(color1.green() + (color2.green() - color1.green()) * t)
        b = int(color1.blue() + (color2.blue() - color1.blue()) * t)
        a = int(color1.alpha() + (color2.alpha() - color1.alpha()) * t)
        return QColor(r, g, b, a)