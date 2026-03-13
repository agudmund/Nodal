#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node_types.py specialized node implementations
-Defines type-specific node classes (warm, about, image, render) with custom rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QLinearGradient, QColor, QPen, QBrush, QPainter, QFont, QPixmap
from utils.theme import Theme


class NodeBase(QGraphicsItem):
    """Base class for all node types with common functionality."""

    def __init__(self, x: float, y: float, title: str = "Node", node_uuid: str = None,
                 node_type: str = "node", full_text: str = "", width: float = None, 
                 height: float = None, ports_visible: bool = True):
        super().__init__()

        # Unique identifier for serialization and connections
        self.uuid = node_uuid if node_uuid else str(uuid.uuid4())

        # Node type and content
        self.node_type = node_type
        self.title = title
        self.full_text = full_text
        self.ports_visible = ports_visible

        # Dimensions - allow override from session, otherwise use theme defaults
        self.width = width if width is not None else Theme.NODE_WIDTH
        self.height = height if height is not None else Theme.NODE_HEIGHT
        self.border_radius = Theme.NODE_RADIUS

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
        """Default paint implementation - override in subclasses for custom rendering."""
        self._paint_body(painter)
        self._paint_text(painter)
        self._paint_ports(painter)

    def _paint_body(self, painter: QPainter):
        """Render node body with gradient and border."""
        body_grad = QLinearGradient(0, 0, 0, self.height)

        if self.isSelected():
            body_grad.setColorAt(0, Theme.adjust_brightness(Theme.ACCENT_SELECTED, 0.4))
            body_grad.setColorAt(1, Theme.NODE_GRADIENT_BOTTOM)
            pen = QPen(Theme.ACCENT_SELECTED, 2)
        else:
            body_grad.setColorAt(0, Theme.NODE_GRADIENT_TOP)
            body_grad.setColorAt(1, Theme.NODE_GRADIENT_BOTTOM)
            pen = QPen(Theme.NODE_BORDER_NORMAL, 1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(body_grad)
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # Rim light (subtle highlight on top edge)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawLine(self.border_radius, 1, self.width - self.border_radius, 1)

    def _paint_text(self, painter: QPainter):
        """Render node title text."""
        painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 11, QFont.Bold))

        # Shadow/Drop-tint for readability
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(0, Theme.BUTTON_TEXT_VERTICAL_OFFSET + 1, self.width, self.height, Qt.AlignCenter, self.title)

        # Main Text
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.drawText(0, Theme.BUTTON_TEXT_VERTICAL_OFFSET, self.width, self.height, Qt.AlignCenter, self.title)

    def _paint_ports(self, painter: QPainter):
        """Render input/output ports if visible."""
        if not self.ports_visible:
            return

        painter.setRenderHint(QPainter.Antialiasing)

        # Output Port (Right side - Copper Core)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Theme.WIRE_CORE)
        painter.drawEllipse(QPointF(self.width, self.height/2), 
                            Theme.SOCKET_RADIUS, Theme.SOCKET_RADIUS)

        # Input Port (Left side - Subtle indentation/socket)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawEllipse(QPointF(0, self.height/2), 
                            Theme.SOCKET_RADIUS, Theme.SOCKET_RADIUS)

    def itemChange(self, change, value):
        """Handle node movement and update connected wires."""
        if change == QGraphicsItem.ItemPositionChange:
            for connection in self.connections:
                connection.update_path()

        return super().itemChange(change, value)

    def get_socket_at(self, local_pos: QPointF):
        """Returns 'input', 'output', or None based on click location."""
        margin = Theme.SOCKET_GRAB_MARGIN

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
    def from_dict(data: dict) -> 'NodeBase':
        """Factory method to create appropriate node type from dictionary."""
        node_type = data.get("type", "node")

        # Dispatch to correct node class based on type
        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        elif node_type == "render":
            return RenderNode.from_dict(data)
        else:
            # Default fallback to base node
            return NodeBase._create_from_dict(data)

    @staticmethod
    def _create_from_dict(data: dict) -> 'NodeBase':
        """Create base node from dict."""
        node = NodeBase(
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


class WarmNode(NodeBase):
    """Text/thought node - displays title and full text content."""

    def __init__(self, x: float, y: float, title: str = "", node_uuid: str = None,
                 full_text: str = "", width: float = None, height: float = None, 
                 ports_visible: bool = False):
        super().__init__(x, y, title=title, node_uuid=node_uuid, node_type="warm",
                         full_text=full_text, width=width, height=height, 
                         ports_visible=ports_visible)

    def _paint_text(self, painter: QPainter):
        """Render both title and full text for warm nodes."""
        painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 11, QFont.Bold))

        # Title with shadow
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(10, 10, self.width - 20, 30, Qt.TextWordWrap, self.title)

        # Title in main color
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.drawText(10, 9, self.width - 20, 30, Qt.TextWordWrap, self.title)

        # Full text in smaller font
        if self.full_text:
            painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 9))
            painter.setPen(QColor(200, 200, 200, 200))
            painter.drawText(10, 40, self.width - 20, self.height - 50, Qt.TextWordWrap, self.full_text)

    @staticmethod
    def from_dict(data: dict) -> 'WarmNode':
        """Create WarmNode from dictionary."""
        node = WarmNode(
            x=data.get("pos_x", 0),
            y=data.get("pos_y", 0),
            title=data.get("title", ""),
            node_uuid=data.get("uuid"),
            full_text=data.get("full_text", ""),
            width=data.get("width"),
            height=data.get("height"),
            ports_visible=data.get("ports_visible", False),
        )
        return node


class AboutNode(NodeBase):
    """Meta/information node - smaller, no ports."""

    def __init__(self, x: float, y: float, title: str = "About", node_uuid: str = None,
                 width: float = None, height: float = None):
        super().__init__(x, y, title=title, node_uuid=node_uuid, node_type="about",
                         width=width, height=height, ports_visible=False)

    def _paint_body(self, painter: QPainter):
        """Render about node with slightly different styling."""
        # Use a darker, more muted gradient for about nodes
        body_grad = QLinearGradient(0, 0, 0, self.height)

        if self.isSelected():
            body_grad.setColorAt(0, Theme.adjust_brightness(Theme.ACCENT_SELECTED, 0.3))
            body_grad.setColorAt(1, QColor(40, 40, 60))
            pen = QPen(Theme.ACCENT_SELECTED, 2)
        else:
            body_grad.setColorAt(0, QColor(50, 50, 70))
            body_grad.setColorAt(1, QColor(30, 30, 45))
            pen = QPen(QColor(100, 100, 120), 1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(body_grad)
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

    @staticmethod
    def from_dict(data: dict) -> 'AboutNode':
        """Create AboutNode from dictionary."""
        node = AboutNode(
            x=data.get("pos_x", 0),
            y=data.get("pos_y", 0),
            title=data.get("title", "About"),
            node_uuid=data.get("uuid"),
            width=data.get("width"),
            height=data.get("height"),
        )
        return node


class ImageNode(NodeBase):
    """Image display node - shows image content."""

    def __init__(self, x: float, y: float, title: str = "", node_uuid: str = None,
                 width: float = None, height: float = None):
        super().__init__(x, y, title=title, node_uuid=node_uuid, node_type="image",
                         width=width, height=height, ports_visible=False)
        self.image = None  # Will load actual image later if available

    def _paint_text(self, painter: QPainter):
        """Image nodes don't render text by default."""
        # Could show title as caption if needed
        if self.title and len(self.title) > 0:
            painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 8))
            painter.setPen(QColor(200, 200, 200, 150))
            painter.drawText(0, self.height - 15, self.width, 15, Qt.AlignCenter, self.title)

    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        """Create ImageNode from dictionary."""
        node = ImageNode(
            x=data.get("pos_x", 0),
            y=data.get("pos_y", 0),
            title=data.get("title", ""),
            node_uuid=data.get("uuid"),
            width=data.get("width"),
            height=data.get("height"),
        )
        return node


class RenderNode(NodeBase):
    """Output/render node - for displaying final results."""

    def __init__(self, x: float, y: float, title: str = "Render", node_uuid: str = None,
                 width: float = None, height: float = None):
        super().__init__(x, y, title=title, node_uuid=node_uuid, node_type="render",
                         width=width, height=height, ports_visible=False)

    def _paint_body(self, painter: QPainter):
        """Render output node with distinct styling (darker)."""
        body_grad = QLinearGradient(0, 0, 0, self.height)

        if self.isSelected():
            body_grad.setColorAt(0, Theme.adjust_brightness(Theme.ACCENT_SELECTED, 0.2))
            body_grad.setColorAt(1, QColor(30, 30, 50))
            pen = QPen(Theme.ACCENT_SELECTED, 2)
        else:
            body_grad.setColorAt(0, QColor(35, 35, 55))
            body_grad.setColorAt(1, QColor(20, 20, 35))
            pen = QPen(QColor(80, 80, 100), 1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(body_grad)
        painter.setPen(pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

    @staticmethod
    def from_dict(data: dict) -> 'RenderNode':
        """Create RenderNode from dictionary."""
        node = RenderNode(
            x=data.get("pos_x", 0),
            y=data.get("pos_y", 0),
            title=data.get("title", "Render"),
            node_uuid=data.get("uuid"),
            width=data.get("width"),
            height=data.get("height"),
        )
        return node
