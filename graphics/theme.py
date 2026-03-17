#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - theme.py color and styling system
-Centralized theme management for consistent UI appearance
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtGui import QColor

class Theme:

    # --- Primary Border (The Consistent Line) ---
    # Single source of truth for all border and line colors across the app
    primaryBorder = QColor("#6b5a47")

    # --- Sizing & Spacing ---
    windowBorderWidth = 1
    handleHeightTop = 65                 # Top toolbar/title bar height (draggable area)
    handleHeightBottom = 100             # Bottom toolbar/button bar height
    dialogTopBarHeight = 35              # Utility dialog top bar height (text only)
    dialogBottomBarHeight = 85           # Utility dialog bottom bar height (button bar)
    windowAnimationDuration = 500        # Milliseconds for minimize animation
    windowRestoreAnimationDuration = 200 # Milliseconds for restore animation (half of minimize)

    # --- Branding (The Soul) ---
    accentNormal = QColor("#3498db")     # Primary Action Blue
    accentSelected = QColor("#00d2ff")   # Glowing Signal Blue
    textPrimary = QColor("#d2d1cf")      # Primary ivory/warm white — buttons, labels, general UI text

    # --- UI Scaffolding ---
    windowBg = QColor("#1e1e1e")
    toolbarBg = QColor("#1e1e1e")
    toolbarBorder = primaryBorder

    # --- Node Dimensions ---
    nodeWidth = 140
    nodeHeight = 90
    nodeRadius = 10
    nodeRoundRadius = 18                 # Corner rounding radius for node body
    nodeShadowBlur = 15                  # Drop shadow blur radius
    nodeShadowColor = QColor(0, 0, 0, 150) # Drop shadow color
    nodeShadowOffsetX = 5.0              # Drop shadow horizontal offset
    nodeShadowOffsetY = 5.0              # Drop shadow vertical offset
    nodeShadowMargin = 22                # Bounding rect shadow margin for click detection
    nodeLodThreshold = 0.3              # LOD gate — below this zoom level detail is hidden
    nodeResizeHandleSize = 12            # Resize triangle size in pixels

    # --- Node Border ---
    nodeBorderWidth = 1                  # Border thickness — normal state
    nodeBorderSelectedScale = 1.25       # Selected border thickness multiplier
    nodeBorderSelected = accentNormal
    nodeDefaultBg = QColor(30, 30, 30, 200) # BaseNode default brush — subclasses override

    # --- Node Hover Animation ---
    nodePulseMin = 400                   # Minimum pulse animation duration in ms
    nodePulseMax = 600                   # Maximum pulse animation duration in ms
    nodePulseScale = 1.025               # Peak scale during pulse — subtle breath effect
    nodeHoverLighten = 125               # Hover pen lightness factor

    # --- Node Port Positioning ---
    portVerticalOffset = -25             # Port vertical nudge from node bottom edge
    portHorizontalNudge = 3.0           # Port horizontal nudge outside node edge

    # --- Ports (Connection Points) ---
    portInputColor = primaryBorder       # Input port blends into node border by design
    portOutputColor = QColor("#8cbea0")  # Cool/mint for outputs
    portGlowDarkness = 140               # Glow effect darkness factor
    portSize = 20                        # Diameter in pixels
    portBorderColor = primaryBorder      # Future-proofed to stay consistent with node borders
    portGlowBlurRadius = 12              # Glow effect blur

    # --- Sockets (Legacy - for backward compatibility) ---
    socketRadius = 5
    socketGrabMargin = 12

    # --- Colors: Scene & Mica ---
    frostColor = QColor(30, 30, 35, 150)
    gridColor = QColor(200, 200, 200, 30)

    # --- Colors: The Nerve System ---
    wireStart = QColor(portOutputColor.red(), portOutputColor.green(), portOutputColor.blue(), 25)
    wireEnd   = QColor(portInputColor.red(),  portInputColor.green(),  portInputColor.blue(),  255)

    # --- Node Type Colors ---
    warmNodeBg = QColor("#2a2a3a")              # Primary thought/text nodes
    aboutNodeBg = QColor(40, 40, 50, 200)       # Meta/info nodes (darker)
    imageNodeBg = QColor(30, 30, 30, 200)       # Image display nodes
    imageCaptionColor = QColor("#a8d0ff")        # Caption text on image nodes — matches WarmNode title tone
    shadowColor = QColor("#282828")             # Node drop shadow

    # --- Node Typography ---
    nodeTitleFontFamily = "Chandler42"
    nodeTitleFontSize = 13
    nodeBodyFontFamily = "Lato"
    nodeBodyFontSize = 9

    # --- Node Update Throttle ---
    nodeUpdateThrottle = 16              # ms — batches connection redraws to ~60 FPS

    # --- Button Styling ---
    buttonFontFamily = "Reey"
    buttonFontSize = 22
    buttonFontBold = False
    buttonTextVerticalOffset = -2
    buttonBorderWidth = 1
    buttonBorderEnabled = False
    buttonMinWidth = 160
    buttonMinHeight = 75

    # --- Button Colors ---
    buttonBg = QColor("#1e1e1e")
    buttonBorder = primaryBorder
    buttonBgHover = QColor("#1e1e1e")
    buttonBorderHover = QColor("#1e1e1e")
    buttonBgInactive = QColor("#1f1f1f")
    buttonBorderInactive = QColor("#4a4a4a")

    # --- ComboBox Styling ---
    comboboxBg = QColor("#1e1e1e")
    comboboxBgOpen = QColor("#2a2a3a")
    comboboxText = QColor("#e0e0ff")
    comboboxBorder = primaryBorder
    comboboxBorderRadius = 8
    comboboxPadding = "6px 10px"
    comboboxFontFamily = "Segoe UI"
    comboboxFontSize = 12
    comboboxFontWeight = "normal"
    comboboxDropdownWidth = 30
    comboboxMinWidth = 200

    # --- Slider Styling ---
    sliderHandleImage = "resources/icons/tester.png"

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
        Example: Theme.adjust_brightness(Theme.accentNormal, 0.8) # 20% darker
        """
        r = max(0, min(255, int(color.red() * factor)))
        g = max(0, min(255, int(color.green() * factor)))
        b = max(0, min(255, int(color.blue() * factor)))
        return QColor(r, g, b, color.alpha())
