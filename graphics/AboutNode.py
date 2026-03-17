#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - aboutNode.py meta/information node
-A small, clean label node for annotations, headings, and context markers
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont
from .BaseNode import BaseNode
from .theme import Theme


class AboutNode(BaseNode):
    """
    A small annotation node for headings, labels, and contextual markers.
    Renders title text only — no body, no emoji, no editor.
    """

    def __init__(self, node_id=0, title="About", pos=QPointF(0, 0),
                 width=200, height=55, uuid=None):
        super().__init__(node_id, title, pos, width, height, uuid)
        self.node_type = "about"
        self.setBrush(Theme.aboutNodeBg)

    # -------------------------------------------------------------------------
    # PAINT
    # -------------------------------------------------------------------------

    def paint_content(self, painter):
        """Render title text centered within the node bounds."""
        padding = 8
        painter.setPen(Theme.textPrimary)
        painter.setFont(QFont(Theme.buttonFontFamily, 10, QFont.Bold))
        painter.drawText(
            padding, padding,
            self.rect().width() - (padding * 2),
            self.rect().height() - (padding * 2),
            Qt.TextWordWrap | Qt.AlignCenter,
            self.title
        )

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """AboutNode has no extra fields beyond base — base serialization is sufficient."""
        return super().to_dict()

    @staticmethod
    def from_dict(data: dict) -> 'AboutNode':
        """Deserialize an AboutNode from session data."""
        node = AboutNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "About"),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 200),
            height=data.get("height", 55),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node
