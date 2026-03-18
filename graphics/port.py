#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - port.py connection port graphics item
-Input/output ports for node connectivity with warm aesthetic styling
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QBrush, QPen
from .Theme import Theme

class Port(QGraphicsEllipseItem):
    """A warm connection port for input/output on nodes 🌿"""

    def __init__(self, parent_node, is_output=False):
        super().__init__(-10, -10, 20, 20, parent_node)

        # Explicitly anchor the identity
        self.is_output = is_output
        self.parent_node = parent_node

        # Color based on port type — single source of truth via Theme
        base_color = Theme.portOutputColor if is_output else Theme.portInputColor
        self.setBrush(QBrush(base_color.lighter(115)))
        self.setPen(QPen(Theme.portBorderColor, 1))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)

        # Connection tracking
        self.edge = None

        # Glow effect around port
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(Theme.portGlowBlurRadius)
        glow.setColor(Theme.primaryBorder)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)