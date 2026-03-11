#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - node.py node item for graphics scene
# Defines the visual representation and behavior of a single node

from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont


class Node(QGraphicsItem):
    """
    A draggable, selectable node item for the graphics scene.
    """

    def __init__(self, x: float, y: float, title: str = "Node"):
        super().__init__()

        self.title = title
        self.width = 120
        self.height = 80
        self.border_radius = 8

        # Set position
        self.setPos(x, y)

        # Make it interactive
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        # Colors
        self.normal_color = QColor(52, 152, 219)  # Blue
        self.selected_color = QColor(41, 128, 185)  # Darker blue
        self.text_color = QColor(255, 255, 255)  # White

    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle of the node."""
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node."""
        # Choose color based on selection state
        brush_color = self.selected_color if self.isSelected() else self.normal_color

        # Draw rounded rectangle background
        painter.setBrush(QBrush(brush_color))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # Draw title text
        painter.setPen(QPen(self.text_color))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, self.width, self.height, Qt.AlignCenter, self.title)

    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
