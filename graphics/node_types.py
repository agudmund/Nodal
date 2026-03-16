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
logger = setup_logger()


class WarmNode(BaseNode):
    """Text/thought node with QGraphicsTextItem, emoji, and note editor."""

    MIN_WIDTH = 180
    MIN_HEIGHT = 60
    MAX_HEIGHT = 1000
    MARGIN = 20

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
         # Calculate minimum width based on title text if width not provided
        if width is None:
            title_font = QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold)
            metrics = QFontMetrics(title_font)
            # Title width + emoji (50px) + padding (20px each side) + some breathing room (20px)
            title_width = metrics.horizontalAdvance(title) if title else 0
            width = max(Theme.nodeWidth, title_width + 90)  # 50 emoji + 40 padding/margins

        if height is None:
            height = Theme.nodeHeight

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "warm"
        self.setBrush(Theme.warmNodeBg)

        # Random emoji for visual personality
        self.emoji = random.choice(["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"])

        # QGraphicsTextItem for emoji
        self.emoji_item = QGraphicsTextItem(self)
        self.emoji_item.setFont(QFont("Segoe UI Emoji", 28))
        self.emoji_item.setPlainText(self.emoji)
        self.emoji_item.setPos(5, 3)

         # QGraphicsTextItem for title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setFont(QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold))
        self.title_item.setDefaultTextColor(QColor("#a8d0ff"))

        # QGraphicsTextItem for body text
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont(Theme.nodeBodyFontFamily, Theme.nodeBodyFontSize))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))

        # Layout update timer
        self._layout_timer = QTimer()
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._sync_content_layout)

        # Track if editor is open
        self._editor = None

        self._sync_content_layout()

    def paint_content(self, painter):
        """Specific dialogue for the WarmNode: Emojis and Thoughts."""
        # Since WarmNode uses child QGraphicsTextItems (self.emoji_item, etc.),
        # we just ensure they are visible. Qt draws child items automatically 
        # AFTER the parent's paint() finishes.
        if not self.emoji_item.isVisible():
            self.emoji_item.show()
            self.title_item.show()
            self.text_item.show()

    def setRect(self, rect):
        """Override to sync content layout when resized."""
        super().setRect(rect)
        self._sync_content_layout()

    def _sync_content_layout(self):
        """Update position and visibility of title and body text items."""
        r = self.rect()

        # === Emoji display (top-left) ===
        # (Will be drawn in paint_content instead)

        # === Title positioning ===
        metrics = QFontMetrics(self.title_item.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, r.width() - 80)
        self.title_item.setPlainText(elided_title)
        self.title_item.setPos(60, 9)

        # === Tiny title-card mode (< 95px height) ===
        if r.height() < 95:
            # Hide body text for small nodes
            self.text_item.setVisible(False)
        else:
            # Show body text
            self.text_item.setVisible(True)

            doc = QTextDocument()
            doc.setDefaultFont(self.text_item.font())
            doc.setPlainText(self.full_text)
            doc.setTextWidth(r.width() - (self.MARGIN * 2))

            self.text_item.setDocument(doc)
            self.text_item.setPos(self.MARGIN, 55)

            # Auto-grow height based on content
            content_needed = doc.size().height() + 85
            if content_needed > r.height() + 8:
                final_h = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, content_needed))
                if abs(r.height() - final_h) > 4:
                    self.prepareGeometryChange()
                    self.setRect(QRectF(r.topLeft(), QSizeF(r.width(), final_h)))

        self.update()

    def open_editor(self):
        """Open the sophisticated note editor."""
        from graphics.note_editor import CozyNoteEditor

        # Get the main window
        main_window = None
        for view in self.scene().views():
            main_window = view.window()
            break

        # Create editor dialog (parented to main window for proper cleanup)
        self._editor = CozyNoteEditor(self.node_id, self.title, self.full_text, parent=main_window)

        # Make editor appear on top without flickering - use raise() and activateWindow()
        # This avoids the expensive setWindowFlags() call that causes screen flicker
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()

        # Connect signals
        self._editor.accepted.connect(self._on_editor_accepted)
        self._editor.rejected.connect(self._on_editor_rejected)

        # Show modeless dialog
        self._editor.setModal(False)

    def _on_editor_accepted(self):
        """User clicked Save → apply changes."""
        if self._editor:
            self.title = self._editor.get_title()
            self.full_text = self._editor.get_text()

            # Recalculate width based on new title (same logic as __init__)
            title_font = QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold)
            metrics = QFontMetrics(title_font)
            title_width = metrics.horizontalAdvance(self.title) if self.title else 0
            new_width = max(Theme.nodeWidth, title_width + 90)

            # Update node width if it changed
            rect = self.rect()
            if abs(rect.width() - new_width) > 0.1:
                self.prepareGeometryChange()
                self.setRect(QRectF(rect.topLeft(), QSizeF(new_width, rect.height())))

            self._sync_content_layout()
            self.update()
            self._editor.mark_as_saved()
            if self.scene():
                self.scene().update()
            self._close_editor()

    def _on_editor_rejected(self):
        """User clicked Cancel → do nothing."""
        self._close_editor()

    def _close_editor(self):
        """Clean up editor reference."""
        if self._editor:
            del self._editor
            self._editor = None

    @staticmethod
    def from_dict(data: dict) -> 'WarmNode':
        """Deserializes a WarmNode using the standard Warehouse keys."""
        node = WarmNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Warm Node"), # Matches 'title' key
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)), # Matches 'pos_x/y'
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class AboutNode(BaseNode):
    """Meta/information node - smaller, no ports."""

    def __init__(self, node_id=0, title="About", full_text="", pos=QPointF(0, 0), 
                 width=200, height=55, uuid=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "about"
        self.setBrush(Theme.aboutNodeBg)

    def paint_content(self, painter):
        """Simple text rendering for about nodes."""
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
    """Image display node - shows image content."""

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
        """Specific dialogue for the ImageNode: Visual Content."""
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
