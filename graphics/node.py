#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node.py node graphics item
-Defines individual node appearance, behavior, and rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QLinearGradient, QColor, QPen, QBrush, QPainter, QFont
from utils.theme import Theme

class Node(QGraphicsItem):
    def __init__(self, x: float, y: float, title: str = "Node"):
        super().__init__()
        self.title = title
        
        # Pull dimensions directly from DNA (Theme)
        self.width = Theme.NODE_WIDTH
        self.height = Theme.NODE_HEIGHT
        self.border_radius = Theme.NODE_RADIUS
        
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Movement tracking for future 'rubbery' wires
        self.connections = []

    def boundingRect(self) -> QRectF:
        # Extra 2px margin to prevent 'anti-aliasing' clipping at the edges
        return QRectF(-2, -2, self.width + 4, self.height + 4)

    def paint(self, painter: QPainter, option, widget):
        # 1. SETUP GRADIENTS
        body_grad = QLinearGradient(0, 0, 0, self.height)
        
        if self.isSelected():
            # Glowing Selection State
            body_grad.setColorAt(0, Theme.adjust_brightness(Theme.ACCENT_SELECTED, 0.4))
            body_grad.setColorAt(1, Theme.NODE_GRADIENT_BOTTOM)
            pen = QPen(Theme.ACCENT_SELECTED, 2)
        else:
            # Solid Obsidian State
            body_grad.setColorAt(0, Theme.NODE_GRADIENT_TOP)
            body_grad.setColorAt(1, Theme.NODE_GRADIENT_BOTTOM)
            pen = QPen(Theme.NODE_BORDER_NORMAL, 1)

        # 2. DRAW BODY
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(body_grad)
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # 3. THE RIM LIGHT (The 'Cushion' effect)
        # A 1px subtle highlight on the top edge to give it depth
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawLine(self.border_radius, 1, self.width - self.border_radius, 1)

        # 4. TEXT RENDERING
        # Using the vertical offset from Theme to handle font-specific baseline shifts
        painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 11, QFont.Bold))
        
        # Shadow/Drop-tint for readability
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(0, Theme.BUTTON_TEXT_VERTICAL_OFFSET + 1, self.width, self.height, Qt.AlignCenter, self.title)
        
        # Main Text
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.drawText(0, Theme.BUTTON_TEXT_VERTICAL_OFFSET, self.width, self.height, Qt.AlignCenter, self.title)

    def itemChange(self, change, value):
        """Notify connections to repaint when the node moves."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)