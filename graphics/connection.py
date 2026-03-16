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
from .theme import Theme

class Connection(QGraphicsPathItem):
    def __init__(self, start_node, end_node=None):
        super().__init__()

        self.floating_point = None 
        self.start_node = start_node
        self.start_node.connections.append(self)
        self.end_node = end_node        
        if self.end_node:  self.end_node.connections.append(self)
        
        self.setZValue(-1)
        self.update_path()

    def update_path(self, mouse_pos=None):
        """Gathers the coordinates and draws the 'Rubbery' Bezier."""
        self.floating_point = mouse_pos
        path = QPainterPath()
        
        # 1. Start Point (Output Port of Start Node)
        # Map from node's local right-edge to scene coordinates
        p1 = self.start_node.mapToScene(self.start_node.rect().width(), self.start_node.rect().height()/2)
        
        if self.end_node:
            # 2. End Point (Input Port of Target Node)
            p2 = self.end_node.mapToScene(0, self.end_node.rect().height()/2)
        elif self.floating_point:
            # 3. Floating Point (Mouse position)
            p2 = self.floating_point
        else:
            return

        path.moveTo(p1)
        
        dx = abs(p2.x() - p1.x()) * 0.5 # Calculate 'Rubbery' Tension
        dx = max(dx, 50) # Ensure the wire stays 'Springy' even when ports are vertically aligned
        
        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
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
        core_pen = QPen(QColor(255, 255, 255, 150), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(core_pen)
        painter.drawPath(self.path())