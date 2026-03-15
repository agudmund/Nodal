#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - port.py connection port graphics item
-Input/output ports for node connectivity with warm aesthetic styling
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QBrush, QPen


class Port(QGraphicsEllipseItem):
    """A warm connection port for input/output on nodes 🌿"""

    def __init__(self, parent_node, is_output=False):
        super().__init__(-10, -10, 20, 20, parent_node)

        # Explicitly anchor the identity
        self.is_output = is_output 
        self.parent_node = parent_node

        # Color based on port type (input=warm/copper, output=cool/mint)
        base_color = QColor(180, 140, 120) if not is_output else QColor(140, 190, 160)
        self.setBrush(QBrush(base_color.lighter(115)))
        self.setPen(QPen(QColor(60, 60, 80, 100), 1))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)

        # Connection tracking (for future wire/edge system)
        self.edge = None

        # Glow effect around port
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(12)
        glow.setColor(base_color.darker(140))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
