#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node.py node graphics item
-Defines individual node appearance, behavior, and rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QLinearGradient, QColor, QPen, QBrush, QPainter, QFont
from utils.theme import Theme

class Node(QGraphicsItem):
    def __init__(self, x: float, y: float, title: str = "Node", node_uuid: str = None, 
                 node_type: str = "node", full_text: str = "", width: float = None, height: float = None, ports_visible: bool = True):
        super().__init__()

        # Unique identifier for serialization and connections
        self.uuid = node_uuid if node_uuid else str(uuid.uuid4())

        # Node type and content
        self.node_type = node_type
        self.title = title
        self.full_text = full_text
        self.ports_visible = ports_visible

        # Dimensions - allow override from session, otherwise use theme defaults
        self.width = width if width is not None else Theme.nodeWidth
        self.height = height if height is not None else Theme.nodeHeight
        self.border_radius = Theme.nodeRadius

        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # Movement tracking for future 'rubbery' wires
        self.connections = []

        # IMPORTANT: This flag allows itemChange to catch movement
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

    def boundingRect(self) -> QRectF:
        # Extra 2px margin to prevent 'anti-aliasing' clipping at the edges
        return QRectF(-2, -2, self.width + 4, self.height + 4)

    def paint(self, painter: QPainter, option, widget):
        # 1. SETUP GRADIENTS
        body_grad = QLinearGradient(0, 0, 0, self.height)
        
        if self.isSelected():
            # Glowing Selection State
            body_grad.setColorAt(0, Theme.adjust_brightness(Theme.accentSelected, 0.4))
            body_grad.setColorAt(1, Theme.nodeGradientBottom)
            pen = QPen(Theme.accentSelected, 2)
        else:
            # Solid Obsidian State
            body_grad.setColorAt(0, Theme.nodeGradientTop)
            body_grad.setColorAt(1, Theme.nodeGradientBottom)
            pen = QPen(Theme.nodeBorderNormal, 1)

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
        painter.setFont(QFont(Theme.buttonFontFamily, 11, QFont.Bold))

        # Shadow/Drop-tint for readability
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(0, Theme.buttonTextVerticalOffset + 1, self.width, self.height, Qt.AlignCenter, self.title)

        # Main Text
        painter.setPen(Theme.textPrimary)
        painter.drawText(0, Theme.buttonTextVerticalOffset, self.width, self.height, Qt.AlignCenter, self.title)

        # 5. THE PORTS (The interface points)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Output Port (Right side - Copper Core)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Theme.portOutputColor)
        painter.drawEllipse(QPointF(self.width, self.height/2), 
                            Theme.socketRadius, Theme.socketRadius)

        # Input Port (Left side - Subtle indentation/socket)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawEllipse(QPointF(0, self.height/2), 
                            Theme.socketRadius, Theme.socketRadius)

    def itemChange(self, change, value):
        """This runs every time the node moves or changes state."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Tell every wire attached to us to redraw itself
            for connection in self.connections:
                connection.update_path()
                
        return super().itemChange(change, value)

    def get_socket_at(self, local_pos: QPointF):
        """Returns 'input', 'output', or None based on click location."""
        margin = Theme.socketGrabMargin

        # Output Socket (Right side)
        if local_pos.x() > self.width - margin:
            return "output"
        # Input Socket (Left side)
        elif local_pos.x() < margin:
            return "input"
        return None

    def to_dict(self) -> dict:
        """Serialize node data to dictionary for JSON storage."""
        pos = self.pos()
        return {
            "type": self.node_type,
            "uuid": self.uuid,
            "title": self.title,
            "full_text": self.full_text,
            "pos_x": pos.x(),
            "pos_y": pos.y(),
            "width": self.width,
            "height": self.height,
            "ports_visible": self.ports_visible,
        }

    @staticmethod
    def from_dict(data: dict) -> 'Node':
        """Deserialize node data from dictionary, preserving all properties."""
        node = Node(
            x=data.get("pos_x", 0),
            y=data.get("pos_y", 0),
            title=data.get("title", "Node"),
            node_uuid=data.get("uuid"),
            node_type=data.get("type", "node"),
            full_text=data.get("full_text", ""),
            width=data.get("width"),
            height=data.get("height"),
            ports_visible=data.get("ports_visible", True),
        )
        return node