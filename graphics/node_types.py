#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node_types.py specialized node implementations
-Type-specific node classes with QGraphicsTextItem, emoji, resizing, and rich rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid as _uuid
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QSizeF, QAbstractAnimation, QTimer
from PySide6.QtGui import QColor, QPen, QFont, QPainter, QBrush, QFontMetrics, QTextDocument, QPainterPath, QTransform
from .theme import Theme
from utils.logger import setup_logger
from . import Port
from . import BaseNode
from . import WarmNode
logger = setup_logger()

class AboutNode(BaseNode):
    """Meta/information node specialization - compact read-only node without ports.
    Used for display-only metadata or information markers in the node graph."""

    def __init__(self, node_id=0, title="About", full_text="", pos=QPointF(0, 0), 
                 width=200, height=55, uuid=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "about"
        self.setBrush(Theme.aboutNodeBg)

    def paint_content(self, painter):
        """Render title text centered with word wrapping in compact node format."""
        padding = 8
        painter.setPen(Theme.textPrimary)
        painter.setFont(QFont(Theme.buttonFontFamily, 10, QFont.Bold))
        painter.drawText(
            padding, padding, 
            self.rect().width() - (padding * 2), self.rect().height() - (padding * 2),
            Qt.TextWordWrap | Qt.AlignCenter, 
            self.title
        )

    @staticmethod
    def from_dict(data: dict) -> 'AboutNode':
        """Create AboutNode from dictionary."""
        node = AboutNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "About"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 200),
            height=data.get("height", 55),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class ImageNode(BaseNode):
    """Image display node specialization - renders pixmap content with optional caption.
    Supports loading and displaying image content with title as caption overlay."""

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
        if width is None:
            width = 200
        if height is None:
            height = 200

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "image"
        self.image = None

    def paint_content(self, painter):
        """Render image pixmap scaled to node bounds, with title caption at bottom if present."""
        if self.image:
            # Draw the image elided within the rounded frame
            painter.drawPixmap(self.rect().toRect(), self.image)

        # Draw the caption if it exists
        if self.title:
            painter.setFont(QFont(Theme.buttonFontFamily, 8))
            painter.setPen(QColor(200, 200, 200, 150))
            painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter, self.title)
    
    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        node = ImageNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Image Node"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        return node
