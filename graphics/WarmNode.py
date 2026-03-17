#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - warmNode.py text and thought node
-A warm, draggable, resizable node for writing, thinking, and bulk markdown import
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import re
import random
from PySide6.QtWidgets import QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QPainterPath, QTextDocument
from .BaseNode import BaseNode
from .Theme import Theme


class WarmNode(BaseNode):
    """
    A warm thought node — emoji, title, and body text as three isolated concerns.
    Supports manual editing, smart title fallback, responsive wrapping, and bulk import.
    """

    MIN_WIDTH  = 180
    MIN_HEIGHT = 60
    MAX_HEIGHT = 1000
    MARGIN     = 20

    # -------------------------------------------------------------------------
    # INITIALISATION
    # -------------------------------------------------------------------------

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0),
                 width=None, height=None, uuid=None):

        # Smart title fallback — derive from first sentence if title is empty
        # Critical for bulk markdown import where naming thousands of nodes is impractical
        resolved_title = self._resolve_title(title, full_text)

        # Calculate minimum width from title metrics if width not provided
        if width is None:
            title_font = QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold)
            metrics = QFontMetrics(title_font)
            title_width = metrics.horizontalAdvance(resolved_title) if resolved_title else 0
            width = max(Theme.nodeWidth, title_width + 90)

        if height is None:
            height = Theme.nodeHeight

        super().__init__(node_id, resolved_title, pos, width, height, uuid)
        self.node_type = "warm"
        self.full_text = full_text
        self.setBrush(Theme.warmNodeBg)

        # ── CONCERN 1: EMOJI ─────────────────────────────────────────────────
        self.emoji = random.choice([
            "🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"
        ])
        self.emoji_item = QGraphicsTextItem(self)
        self.emoji_item.setFont(QFont("Segoe UI Emoji", 28))
        self.emoji_item.setPlainText(self.emoji)
        self.emoji_item.setPos(5, 3)

        # ── CONCERN 2: TITLE ─────────────────────────────────────────────────
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setFont(QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold))
        self.title_item.setDefaultTextColor(Theme.imageCaptionColor)

        # ── CONCERN 3: BODY TEXT ─────────────────────────────────────────────
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont(Theme.nodeBodyFontFamily, Theme.nodeBodyFontSize))
        self.text_item.setDefaultTextColor(Theme.textPrimary)

        # Throttle timer — prevents heavy wrap recalculation on every mouse move pixel
        self._resize_throttle_timer = QTimer()
        self._resize_throttle_timer.setSingleShot(True)
        self._resize_throttle_timer.timeout.connect(self._sync_content_layout)

        # Editor reference
        self._editor = None

        # Document cache tracking — avoids expensive QTextDocument churn on every layout sync
        self._last_full_text = None

        self._sync_content_layout()

    # -------------------------------------------------------------------------
    # SMART TITLE RESOLUTION
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_title(title: str, full_text: str) -> str:
        """
        Derive a display title from available content.
        Priority: explicit title → first sentence of body → fallback.
        Uses regex sentence boundary splitting to avoid mid-word cuts.
        """
        if title and title.strip():
            return title.strip()

        if full_text and full_text.strip():
            first_sentence = re.split(r'[.!?]\s*|\n', full_text.strip(), maxsplit=1)[0].strip()
            if first_sentence:
                return first_sentence

        return "All Glory"

    # -------------------------------------------------------------------------
    # CONCERN 1: EMOJI
    # -------------------------------------------------------------------------

    def set_emoji(self, emoji: str):
        """Set a specific emoji, or call randomise_emoji() for a random one."""
        self.emoji = emoji
        self.emoji_item.setPlainText(emoji)

    def randomise_emoji(self):
        """Pick a new random emoji."""
        self.set_emoji(random.choice([
            "🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"
        ]))

    # -------------------------------------------------------------------------
    # CONCERN 2: TITLE
    # -------------------------------------------------------------------------

    def _refresh_title(self):
        """
        Update the title display — elided to fit node width.
        Preserves the full title internally, only truncates visually.
        """
        if not self.title:
            self.title_item.setPlainText("")
            return

        max_px = self.rect().width() - 80  # 80 = emoji width + padding
        metrics = QFontMetrics(self.title_item.font())
        elided = metrics.elidedText(self.title, Qt.ElideRight, max_px)
        self.title_item.setPlainText(elided)
        self.title_item.setPos(60, 9)

    # -------------------------------------------------------------------------
    # CONCERN 3: BODY TEXT
    # -------------------------------------------------------------------------

    def _refresh_body(self):
        """
        Responsive body text wrap — width tracks node rect so resizing
        never orphans text outside the frame.
        Document is cached and only recreated when width changes.
        Text is only set when content actually changes — avoids QTextDocument churn
        which was causing 60+ expensive operations per second during interaction.
        """
        if not self.full_text:
            self.text_item.setPlainText("")
            return

        wrap_width = max(100, self.rect().width() - (self.MARGIN * 2))

        doc = self.text_item.document()
        if not doc or doc.textWidth() != wrap_width:
            doc = QTextDocument()
            doc.setDefaultFont(self.text_item.font())
            if self._last_full_text != self.full_text:
                doc.setPlainText(self.full_text)
                self._last_full_text = self.full_text
            doc.setTextWidth(wrap_width)
            self.text_item.setDocument(doc)
        elif self._last_full_text != self.full_text:
            doc.setPlainText(self.full_text)
            self._last_full_text = self.full_text

        self.text_item.setPos(self.MARGIN, 55)

    # -------------------------------------------------------------------------
    # LAYOUT
    # -------------------------------------------------------------------------

    def _sync_content_layout(self):
        """
        Master layout pass — refreshes all three concerns and handles
        auto-grow height based on body content.
        """
        r = self.rect()

        self._refresh_title()

        # Tiny title-card mode — body hidden below threshold height
        if r.height() < 95:
            self.text_item.setVisible(False)
        else:
            self.text_item.setVisible(True)
            self._refresh_body()

            # Auto-grow: expand height if content needs more space
            doc = self.text_item.document()
            if doc:
                content_needed = doc.size().height() + 85
                if content_needed > r.height() + 8:
                    final_h = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, content_needed))
                    if abs(r.height() - final_h) > 4:
                        self.prepareGeometryChange()
                        self.setRect(QRectF(r.topLeft(), QSizeF(r.width(), final_h)))

        self.update()

    def setRect(self, rect):
        """Sync content layout whenever the node rect changes."""
        super().setRect(rect)
        self._sync_content_layout()

    # -------------------------------------------------------------------------
    # PAINT
    # -------------------------------------------------------------------------

    def paint_content(self, painter):
        """
        WarmNode specialist handoff — emoji, title and body are
        QGraphicsTextItem children so Qt draws them automatically after
        the parent paint() finishes. We just ensure visibility here.
        """
        if not self.emoji_item.isVisible():
            self.emoji_item.show()
            self.title_item.show()
            self.text_item.show()

    def shape(self):
        """Precise rounded rect shape for click detection and collision."""
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.round_radius, self.round_radius)
        return path

    # -------------------------------------------------------------------------
    # DOUBLE CLICK — opens note editor
    # -------------------------------------------------------------------------

    def on_double_click(self, event):
        """Open the note editor on left double-click."""
        from graphics.NoteEditor import CozyNoteEditor

        main_window = None
        for view in self.scene().views():
            main_window = view.window()
            break

        self._editor = CozyNoteEditor(
            self.node_id, self.title, self.full_text, parent=main_window
        )
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()
        self._editor.accepted.connect(self._on_editor_accepted)
        self._editor.rejected.connect(self._on_editor_rejected)
        self._editor.setModal(False)

    def _on_editor_accepted(self):
        """Apply changes from the note editor."""
        if not self._editor:
            return

        new_title = self._editor.get_title()
        new_text  = self._editor.get_text()

        # Re-resolve title in case editor was saved with empty title field
        self.title     = self._resolve_title(new_title, new_text)
        self.full_text = new_text

        # Recalculate width from new title
        title_font = QFont(Theme.nodeTitleFontFamily, Theme.nodeTitleFontSize, QFont.Bold)
        metrics = QFontMetrics(title_font)
        title_width = metrics.horizontalAdvance(self.title) if self.title else 0
        new_width = max(Theme.nodeWidth, title_width + 90)

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
        """Discard changes."""
        self._close_editor()

    def _close_editor(self):
        """Clean up editor reference."""
        if self._editor:
            del self._editor
            self._editor = None

    # -------------------------------------------------------------------------
    # RESIZE — throttled for performance
    # -------------------------------------------------------------------------

    def mouseMoveEvent(self, event):
        """
        Throttled resize — heavy layout recalculation is gated behind a timer
        so dragging at speed stays responsive even on slow hardware.
        """
        if self._is_resizing:
            if not self._resize_throttle_timer.isActive():
                self._sync_content_layout()
                self._resize_throttle_timer.start(120)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Final layout sync after resize completes."""
        self._resize_throttle_timer.stop()
        super().mouseReleaseEvent(event)
        if not self._is_resizing:
            self._sync_content_layout()

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Extend base serialization with WarmNode-specific full_text.
        Emoji is intentionally excluded — randomises on every session load to keep the canvas fresh."""
        data = super().to_dict()
        data["full_text"] = self.full_text
        return data

    @staticmethod
    def from_dict(data: dict) -> 'WarmNode':
        """Deserialize a WarmNode from session data."""
        node = WarmNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", ""),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0.0), data.get("pos_y", 0.0)),
            width=float(data["width"]) if data.get("width") is not None else None,
            height=float(data["height"]) if data.get("height") is not None else None,
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node
