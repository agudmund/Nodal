#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - connection.py bezier connection rendering
-Visual connections between nodes with dynamic bezier curves and hover effects
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QLinearGradient, QPainter, QBrush
from PySide6.QtCore import Qt, QPointF
from .Theme import Theme

class Connection(QGraphicsPathItem):
    def __init__(self, start_node, end_node=None):
        super().__init__()

        self.floating_point = None 
        self.start_node = start_node
        self.start_node.connections.append(self)
        self.end_node = end_node        
        if self.end_node:  self.end_node.connections.append(self)

        # Cache last positions to detect meaningful changes
        self._last_p1 = None
        self._last_p2 = None
        self._cached_path = None

        self.setZValue(-1)
        self.update_path()

    def update_path(self, mouse_pos=None):
        """Update bezier path only if endpoints have moved significantly."""
        self.floating_point = mouse_pos

        # Start point — output port scene position
        p1 = self.start_node.mapToScene(self.start_node.output_port.pos())

        if self.end_node:
            # End point — input port scene position
            p2 = self.end_node.mapToScene(self.end_node.input_port.pos())
        elif self.floating_point:
            p2 = self.floating_point
        else:
            return

        # Only recalculate if endpoints moved more than 1 pixel (prevent floating point jitter)
        if self._last_p1 and self._last_p2:
            dist1 = (p1.x() - self._last_p1.x()) ** 2 + (p1.y() - self._last_p1.y()) ** 2
            dist2 = (p2.x() - self._last_p2.x()) ** 2 + (p2.y() - self._last_p2.y()) ** 2
            if dist1 < 2 and dist2 < 2:  # Threshold: 1 pixel movement
                return  # Skip recalculation for tiny movements

        # Cache the new positions
        self._last_p1 = p1
        self._last_p2 = p2

        # Build the bezier path
        path = QPainterPath()
        path.moveTo(p1)

        dx = abs(p2.x() - p1.x()) * 0.5  # Calculate 'Rubbery' Tension
        dx = max(dx, 50)  # Ensure the wire stays 'Springy' even when ports are vertically aligned

        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())

        path.cubicTo(ctrl1, ctrl2, p2)
        self._cached_path = path
        self.setPath(path)

    def paint(self, painter, option, widget):
        if not self.path(): return

        painter.setRenderHint(QPainter.Antialiasing)
        
        p1 = self.path().pointAtPercent(0)
        p2 = self.path().pointAtPercent(1)
        
        grad = QLinearGradient(p1, p2)
        grad.setColorAt(0, Theme.wireStart)
        grad.setColorAt(1, Theme.wireEnd)
        
        # Drawing the "Glow" line first (thicker, lower alpha)
        glow_pen = QPen(QBrush(grad), 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(self.path())

        # Drawing the "Core" line second (thinner, higher alpha)
        core_pen = QPen(Theme.from_hex('#ffffff', 150), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(core_pen)
        painter.drawPath(self.path())