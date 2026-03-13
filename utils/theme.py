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
    WINDOW_BORDER_WIDTH = 1
    HANDLE_HEIGHT = 70  # Toolbar height

    # --- Branding (The Soul) ---
    ACCENT_NORMAL = QColor("#3498db")   # Primary Action Blue
    ACCENT_SELECTED = QColor("#00d2ff") # Glowing Signal Blue
    TEXT_PRIMARY = QColor("#ffffff")
    
    # --- UI Scaffolding ---
    WINDOW_BG = QColor("#1e1e1e")
    TOOLBAR_BG = QColor("#1e1e1e")
    TOOLBAR_BORDER = QColor("#6b5a47") # Consider changing to ACCENT_NORMAL?
    
    # --- Node Dimensions ---
    NODE_WIDTH = 140
    NODE_HEIGHT = 90
    NODE_RADIUS = 10
    
    # --- Sockets (Ports) ---
    SOCKET_RADIUS = 5
    SOCKET_GRAB_MARGIN = 12 
    
    # --- Colors: Scene & Mica ---
    FROST_COLOR = QColor(30, 30, 35, 150)
    GRID_COLOR = QColor(200, 200, 200, 30)

    # --- Colors: Node Aesthetics ---
    NODE_GRADIENT_TOP = QColor(55, 55, 60, 255)
    NODE_GRADIENT_BOTTOM = QColor(25, 25, 30, 255)
    NODE_BORDER_NORMAL = QColor(255, 255, 255, 40)
    NODE_BORDER_SELECTED = ACCENT_NORMAL

    # --- Button Styling ---
    BUTTON_FONT_FAMILY = "Segoe UI"
    BUTTON_FONT_SIZE = 10
    BUTTON_FONT_BOLD = False
    BUTTON_TEXT_VERTICAL_OFFSET = -2
    BUTTON_BORDER_WIDTH = 2
    BUTTON_BORDER_ENABLED = True

    # --- Button Colors ---
    BUTTON_BG = QColor("#3a3a3a")
    BUTTON_BORDER = QColor("#1e1e1e")
    BUTTON_BG_HOVER = QColor("#1e1e1e")
    BUTTON_BORDER_HOVER = QColor("#6b5a47")
    BUTTON_BG_INACTIVE = QColor("#1f1f1f")
    BUTTON_BORDER_INACTIVE = QColor("#4a4a4a")

    # --- ComboBox Styling ---
    COMBOBOX_BG = QColor("#1e1e1e")
    COMBOBOX_BG_OPEN = QColor("#2a2a3a")
    COMBOBOX_TEXT = QColor("#e0e0ff")
    COMBOBOX_BORDER = QColor("#6b5a47")
    COMBOBOX_BORDER_RADIUS = 8
    COMBOBOX_PADDING = "6px 10px"
    COMBOBOX_FONT_FAMILY = "Segoe UI"
    COMBOBOX_FONT_SIZE = 12
    COMBOBOX_FONT_WEIGHT = "normal"
    COMBOBOX_DROPDOWN_WIDTH = 30
    COMBOBOX_MIN_WIDTH = 200

    # --- Colors: The Nerve System (Electrical Copper) ---
    # A broad, faint glow to simulate light scattering on the 'Mica' surface
    WIRE_GLOW = QColor(155, 126, 94, 60) 
    # The sharp, energetic signal core
    WIRE_CORE = QColor(155, 126, 94, 255)

    @staticmethod
    def lerp(color1: QColor, color2: QColor, t: float) -> QColor:
        """Linear interpolation between two colors."""
        t = max(0.0, min(1.0, t))
        return QColor(
            int(color1.red() + (color2.red() - color1.red()) * t),
            int(color1.green() + (color2.green() - color1.green()) * t),
            int(color1.blue() + (color2.blue() - color1.blue()) * t),
            int(color1.alpha() + (color2.alpha() - color1.alpha()) * t)
        )

    @staticmethod
    def get_alpha(color: QColor, alpha: int) -> QColor:
        return QColor(color.red(), color.green(), color.blue(), alpha)

    @staticmethod
    def adjust_brightness(color: QColor, factor: float) -> QColor:
        """
        factor > 1.0 makes it brighter, < 1.0 makes it darker.
        Example: Theme.adjust_brightness(Theme.ACCENT_NORMAL, 0.8) # 20% darker
        """
        r = max(0, min(255, int(color.red() * factor)))
        g = max(0, min(255, int(color.green() * factor)))
        b = max(0, min(255, int(color.blue() * factor)))
        return QColor(r, g, b, color.alpha())