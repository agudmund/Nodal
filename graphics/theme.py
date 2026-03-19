#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - Theme.py color and styling system
-Centralized theme management for consistent UI appearance for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtGui import QColor

class Theme:

    # =========================================================================
    # GLOBAL
    # =========================================================================

    # --- Primary Border (The Consistent Line) ---
    # Single source of truth for all border and line colors across the app
    primaryBorder = QColor("#6b5a47")

    # --- Branding (The Soul) ---
    accentNormal   = QColor("#3498db")   # Primary Action Blue
    accentSelected = QColor("#00d2ff")   # Glowing Signal Blue
    textPrimary    = QColor("#d2d1cf")   # Primary ivory/warm white — buttons, labels, general UI text

    # =========================================================================
    # WINDOW & UI SCAFFOLDING
    # =========================================================================

    windowBg              = QColor("#1e1e1e")
    windowBorderWidth     = 1
    windowAnimationDuration        = 500   # Milliseconds for minimize animation
    windowRestoreAnimationDuration = 200   # Milliseconds for restore animation (half of minimize)

    toolbarBg     = QColor("#1e1e1e")
    toolbarBorder = primaryBorder

    handleHeightTop    = 35    # Top toolbar/title bar height (draggable area)
    handleHeightBottom = 100   # Bottom toolbar/button bar height

    dialogTopBarHeight    = 35   # Utility dialog top bar height (text only)
    dialogBottomBarHeight = 85   # Utility dialog bottom bar height (button bar)

    # =========================================================================
    # NODES
    # =========================================================================

    # --- Dimensions & Geometry ---
    nodeWidth       = 140
    nodeHeight      = 90
    nodeRadius      = 10
    nodeMinWidth    = 120.0   # Minimum width during resize
    nodeMinHeight   = 50.0    # Minimum height during resize
    nodeRoundRadius = 18      # Corner rounding radius for node body

    # --- Shadow ---
    nodeShadowBlur    = 15
    nodeShadowColor   = QColor(0, 0, 0, 150)
    nodeShadowOffsetX = 5.0
    nodeShadowOffsetY = 5.0
    nodeShadowMargin  = 22    # Bounding rect shadow margin for click detection

    # --- Border ---
    nodeBorderWidth         = 1      # Border thickness — normal state
    nodeBorderSelectedScale = 1.25   # Selected border thickness multiplier
    nodeBorderSelected      = accentNormal
    nodeDefaultBg           = QColor(30, 30, 30, 200)   # BaseNode default brush — subclasses override

    # --- Resize Grip ---
    nodeResizeHandleSize = 12                            # Grab area size in pixels
    resizeGripImage      = "resources/icons/tester.png" # Swap for custom grip asset anytime
    _resizeGripPixmap    = None                          # Lazy loaded after QApplication exists

    # --- LOD & Performance ---
    nodeLodThreshold   = 0.3   # LOD gate — below this zoom level detail is hidden
    nodeUpdateThrottle = 16    # ms — batches connection redraws to ~60 FPS

    # --- Hover & Pulse Animation ---
    nodePulseMin   = 400    # Minimum pulse animation duration in ms
    nodePulseMax   = 600    # Maximum pulse animation duration in ms
    nodePulseScale = 1.05  # Peak scale during pulse — subtle breath effect

    # --- Node Type Colors ---
    warmNodeBg        = QColor("#2a2a3a")       # Primary thought/text nodes
    aboutNodeBg       = QColor(40, 40, 50, 200) # Meta/info nodes (darker)
    imageNodeBg       = QColor(30, 30, 30, 200) # Image display nodes
    imageCaptionColor = QColor("#a8d0ff")        # Caption text — matches WarmNode title tone

    # --- Node Typography ---
    nodeTitleFontFamily = "Chandler42"
    nodeTitleFontSize   = 13
    nodeBodyFontFamily  = "Lato"
    nodeBodyFontSize    = 9

    # =========================================================================
    # PORTS & CONNECTIONS
    # =========================================================================

    # --- Port Colors ---
    portInputColor  = primaryBorder      # Input port blends into node border by design
    portOutputColor = QColor("#8cbea0")  # Cool/mint for outputs
    portBorderColor = primaryBorder      # Future-proofed to stay consistent with node borders

    # --- Port Sizing & Glow ---
    portSize           = 20    # Diameter in pixels
    portGlowBlurRadius = 12    # Glow effect blur radius
    # portGlowDarkness   = QColor("#8cbea0")

    # --- Port Positioning ---
    portVerticalOffset  = 45   # Port vertical nudge from node bottom edge
    portHorizontalNudge = 3.0   # Port horizontal nudge outside node edge

    # --- Sockets (Legacy - for backward compatibility) ---
    socketRadius     = 5
    socketGrabMargin = 12

    # --- Wires (The Nerve System) ---
    wireStart = QColor(portOutputColor.red(), portOutputColor.green(), portOutputColor.blue(), 25)
    wireEnd   = QColor(portInputColor.red(),  portInputColor.green(),  portInputColor.blue(),  255)

    # =========================================================================
    # SCENE & BACKGROUND
    # =========================================================================

    frostColor = QColor(30, 30, 35, 150)
    gridColor  = QColor(200, 200, 200, 30)
    debugNodeOverlay = False   # Toggled at startup from Settings — shows boundingRect/shape/port crosses

    # =========================================================================
    # BUTTONS
    # =========================================================================

    buttonFontFamily         = "Reey"
    buttonFontSize           = 22
    buttonFontBold           = False
    buttonTextVerticalOffset = -2
    buttonBorderWidth        = 1
    buttonBorderEnabled      = False
    buttonMinWidth           = 160
    buttonMinHeight          = 75

    buttonBg             = QColor("#1e1e1e")
    buttonBorder         = primaryBorder
    buttonBgHover        = QColor("#1e1e1e")
    buttonBorderHover    = QColor("#1e1e1e")
    buttonBgInactive     = QColor("#1f1f1f")
    buttonBorderInactive = QColor("#4a4a4a")

    # =========================================================================
    # COMBOBOX
    # =========================================================================

    comboboxBg            = QColor("#1e1e1e")
    comboboxBgOpen        = QColor("#2a2a3a")
    comboboxText          = QColor("#e0e0ff")
    comboboxBorder        = primaryBorder
    comboboxBorderRadius  = 9
    comboboxPadding       = "3px 12px"
    comboboxFontFamily    = "Segoe UI"
    comboboxFontSize      = 9
    comboboxFontWeight    = "normal"
    comboboxDropdownWidth = 30
    comboboxMinWidth      = 350

    # =========================================================================
    # SLIDER
    # =========================================================================

    sliderHandleImage = "resources/icons/tester.png"

    # =========================================================================
    # STATIC HELPERS
    # =========================================================================

    @staticmethod
    def getResizeGripPixmap():
        """Lazy load resize grip pixmap — safe to call after QApplication is created."""
        if Theme._resizeGripPixmap is None:
            from PySide6.QtGui import QPixmap
            Theme._resizeGripPixmap = QPixmap(Theme.resizeGripImage)
        return Theme._resizeGripPixmap

    @staticmethod
    def from_hex(hex_str: str, alpha: int = 255) -> QColor:
        """Build a QColor from a hex string with an optional alpha value.
        Example: Theme.from_hex('#3498db', 180)
        """
        c = QColor(hex_str)
        c.setAlpha(alpha)
        return c

    @staticmethod
    def with_alpha(color: QColor, alpha: int) -> QColor:
        """Return a copy of color with a specific alpha value.
        Example: Theme.with_alpha(Theme.frostColor, 100)
        """
        return QColor(color.red(), color.green(), color.blue(), alpha)

    @staticmethod
    def get_alpha(color: QColor, alpha: int) -> QColor:
        """Alias for with_alpha — kept for backward compatibility."""
        return Theme.with_alpha(color, alpha)

    @staticmethod
    def darken(color: QColor, factor: int = 140) -> QColor:
        """Return a darker copy of color.
        factor > 100 = darker, default 140 matches port glow darkness.
        Example: Theme.darken(Theme.portOutputColor)
        """
        return color.darker(factor)

    @staticmethod
    def lighten(color: QColor, factor: int = 125) -> QColor:
        """Return a lighter copy of color.
        factor > 100 = lighter, default 125 matches hover pen lightening.
        Example: Theme.lighten(Theme.primaryBorder)
        """
        return color.lighter(factor)

    @staticmethod
    def adjust_brightness(color: QColor, factor: float) -> QColor:
        """Return a copy of color with brightness scaled by factor.
        factor > 1.0 = brighter, < 1.0 = darker.
        Example: Theme.adjust_brightness(Theme.accentNormal, 0.8)
        """
        r = max(0, min(255, int(color.red()   * factor)))
        g = max(0, min(255, int(color.green() * factor)))
        b = max(0, min(255, int(color.blue()  * factor)))
        return QColor(r, g, b, color.alpha())
