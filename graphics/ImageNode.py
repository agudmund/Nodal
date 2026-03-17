#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - imageNode.py image display node
-A resizable node for displaying images with an optional caption
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont
from .BaseNode import BaseNode
from .theme import Theme


class ImageNode(BaseNode):
    """
    An image display node — renders a pixmap within its rounded frame
    with an optional title caption at the bottom.
    Double-click to browse for an image.
    """

    def __init__(self, node_id=0, title="", pos=QPointF(0, 0),
                 width=200, height=200, uuid=None):
        super().__init__(node_id, title, pos, width, height, uuid)
        self.node_type = "image"
        self.image = None
        self.setBrush(Theme.imageNodeBg)

    # -------------------------------------------------------------------------
    # PAINT
    # -------------------------------------------------------------------------

    def paint_content(self, painter):
        """Render image within node bounds, with title as caption if present."""
        if self.image:
            painter.drawPixmap(self.rect().toRect(), self.image)

        if self.title:
            painter.setFont(QFont(Theme.buttonFontFamily, 8))
            painter.setPen(Theme.imageCaptionColor)
            painter.drawText(
                self.rect(),
                Qt.AlignBottom | Qt.AlignHCenter,
                self.title
            )

    # -------------------------------------------------------------------------
    # DOUBLE CLICK — browse for image
    # -------------------------------------------------------------------------

    def on_double_click(self, event):
        """Open file browser to select an image."""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            None, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if path:
            from PySide6.QtGui import QPixmap
            self.image = QPixmap(path)
            self.update()

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """ImageNode stores image path rather than pixel data."""
        data = super().to_dict()
        data["image_path"] = self.image.cacheKey() if self.image else None
        return data

    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        """Deserialize an ImageNode from session data."""
        node = ImageNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 200),
            height=data.get("height", 200),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node
