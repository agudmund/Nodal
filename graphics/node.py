#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - node.py node item for graphics scene
# Defines the visual representation and behavior of a single node

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont, QCursor

# Node color constants (defined in nodal.qss)
NODE_COLOR_NORMAL = QColor(52, 152, 219)      # --node-normal: #3498db
NODE_COLOR_SELECTED = QColor(41, 128, 185)    # --node-selected: #2980b9
NODE_COLOR_TEXT = QColor(255, 255, 255)       # --node-text: #ffffff


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
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle of the node."""
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node."""
        # Choose color based on selection state
        brush_color = NODE_COLOR_SELECTED if self.isSelected() else NODE_COLOR_NORMAL

        # Draw rounded rectangle background
        painter.setBrush(QBrush(brush_color))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # Draw title text
        painter.setPen(QPen(NODE_COLOR_TEXT))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, self.width, self.height, Qt.AlignCenter, self.title)

    def mousePressEvent(self, event):
        """Handle mouse press - show closed hand cursor when dragging."""
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - show open hand cursor."""
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        """Handle hover enter - show open hand cursor."""
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Handle hover leave - reset to default cursor."""
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)
