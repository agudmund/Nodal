#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - ImageNode.py image display node
-A resizable node for displaying images with an optional caption for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import base64
from PySide6.QtWidgets import QGraphicsTextItem, QFileDialog, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QFont, QPixmap, QFontMetrics, QPainterPath
from .BaseNode import BaseNode
from .Theme import Theme


class CaptionTextItem(QGraphicsTextItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        # Accept Backspace/Delete and all editing keys to prevent node deletion
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            super().keyPressEvent(event)
            event.accept()
            return
        super().keyPressEvent(event)


class ImageNode(BaseNode):
    """
    An image display node — renders a pixmap within its rounded frame
    with an editable title caption below the image.

    Entry points:
        Double-click image area  — opens a file browser to load an image.
        Double-click caption     — enters inline title edit mode.
        Drop                     — Scene.dropEvent creates an ImageNode from a dragged file.
        from_dict()              — restores a node from base64 session data.

    Resize:
        Corner drag (inherited from BaseNode) updates both the node rect and the
        scaled pixmap display. The source pixmap is kept at full resolution;
        only the display rect changes.

    Serialization:
        Image data travels as base64 in the session JSON under the key
        'image_b64'. This keeps sessions fully self-contained with no
        external path references.
    """

    MIN_WIDTH      = 120
    MIN_HEIGHT     = 100
    CAPTION_HEIGHT = 28     # Reserved pixels below image for the title label
    IMAGE_PADDING  = 6      # Inset from node edges to the image display area
    CAPTION_MARGIN = 8      # Horizontal padding on the caption text

    # -------------------------------------------------------------------------
    # INITIALISATION
    # -------------------------------------------------------------------------

    def __init__(self, node_id: int = 0, title: str = "", pos: QPointF = QPointF(0, 0),
                 width: float = 260.0, height: float = 220.0, uuid: str = None):
        super().__init__(node_id=node_id, title=title, pos=pos, width=width, height=height, uuid=uuid)
        self.node_type = "image"

        # Source pixmap — full resolution, never scaled.
        self._pixmap: QPixmap | None = None

        self.setBrush(Theme.imageNodeBg)

        # ── Caption label ─────────────────────────────────────────────────────
        # NoTextInteraction by default so normal drag/select events reach the parent.
        # Interaction is enabled on demand during inline edit mode.
        # self._caption_item = QGraphicsTextItem(self)
        self._caption_item = CaptionTextItem(self)
        self._caption_item.setFont(QFont(Theme.buttonFontFamily, 8))
        self._caption_item.setDefaultTextColor(Theme.imageCaptionColor)
        self._caption_item.setTextWidth(self.rect().width() - self.CAPTION_MARGIN * 2)
        self._caption_item.setTextInteractionFlags(Qt.NoTextInteraction)
        # Suppress the focus/selection rectangle by matching it to the node background.
        # imageNodeBg as a hex string so QTextDocument's CSS parser can read it.
        _bg = Theme.imageNodeBg
        _bg_hex = f"#{_bg.red():02x}{_bg.green():02x}{_bg.blue():02x}"
        self._caption_item.document().setDefaultStyleSheet(
            f"* {{ selection-background-color: {_bg_hex}; selection-color: {_bg_hex}; }}"
        )

        self._is_editing_caption = False

        self._sync_caption()

    # -------------------------------------------------------------------------
    # PUBLIC — load image from a file path
    # -------------------------------------------------------------------------

    def load_from_path(self, path: str):
        """
        Load a pixmap from a file path and refresh the display.
        Sets the title to the filename stem if the node has no title yet.
        Called by both the double-click browser and Scene.dropEvent.
        """
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return

        self._pixmap = pixmap

        if not self.title:
            import os
            self.title = os.path.splitext(os.path.basename(path))[0]

        self._sync_caption()
        self.update()

        if self.scene():
            self.scene().set_dirty(True)

    # -------------------------------------------------------------------------
    # GEOMETRY HELPERS
    # -------------------------------------------------------------------------

    def _image_rect(self) -> QRectF:
        """
        The area available to the image — node rect inset by IMAGE_PADDING on
        all sides, with an additional CAPTION_HEIGHT inset at the bottom.
        Uniform padding keeps the image clear of the rounded node corners at
        any node scale.
        """
        r = self.rect()
        p = self.IMAGE_PADDING
        return QRectF(
            r.x() + p,
            r.y() + p,
            r.width()  - p * 2,
            r.height()  - p * 2 - self.CAPTION_HEIGHT
        )

    # -------------------------------------------------------------------------
    # CAPTION — sync and inline edit
    # -------------------------------------------------------------------------

    def _sync_caption(self):
        """
        Position and update the caption label.
        In view mode: elided plain text, no interaction.
        In edit mode: full text, interaction enabled — managed by _start_caption_edit.
        """
        r = self.rect()

        if not self._is_editing_caption:
            if self.title:
                max_px = int(r.width() - self.CAPTION_MARGIN * 2)
                metrics = QFontMetrics(self._caption_item.font())
                elided = metrics.elidedText(self.title, Qt.ElideRight, max_px)
                self._caption_item.setPlainText(elided)
            else:
                self._caption_item.setPlainText("")

        self._caption_item.setTextWidth(r.width() - self.CAPTION_MARGIN * 2)
        caption_y = r.height() - self.CAPTION_HEIGHT + (self.CAPTION_HEIGHT - 16) // 2
        self._caption_item.setPos(self.CAPTION_MARGIN, caption_y)

    def _start_caption_edit(self):
        """
        Switch the caption into inline edit mode.
        Shows full unelided title, enables interaction, selects all so
        the user can type a replacement immediately.

        Focus chain: NodeGraphicsView has Qt.NoFocus by design to prevent the
        canvas stealing focus from the toolbar during normal use. We temporarily
        lift this to StrongFocus so the scene can receive key events, then hand
        focus to the caption item via scene.setFocusItem(). On commit or cancel,
        NoFocus is restored so normal behaviour is unaffected.
        """
        self._is_editing_caption = True
        self._caption_item.setPlainText(self.title)
        self._caption_item.setTextInteractionFlags(Qt.TextEditorInteraction)

        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            view.setFocusPolicy(Qt.StrongFocus)
            view.setFocus()

        self.scene().setFocusItem(self._caption_item)
        self._caption_item.setFocus()  # Ensure keyboard focus for text editing

        cursor = self._caption_item.textCursor()
        cursor.select(cursor.SelectionType.Document)
        self._caption_item.setTextCursor(cursor)

    def _commit_caption_edit(self):
        """
        Commit the edited caption back to self.title and return to view mode.
        Restores the view's NoFocus policy so the canvas doesn't steal focus
        from toolbar widgets after editing is done.
        """
        if not self._is_editing_caption:
            return
        new_title = self._caption_item.toPlainText().strip()
        self.title = new_title if new_title else self.title
        self._is_editing_caption = False
        self._caption_item.setTextInteractionFlags(Qt.NoTextInteraction)
        self._caption_item.clearFocus()
        if self.scene() and self.scene().views():
            self.scene().views()[0].setFocusPolicy(Qt.NoFocus)
        self._sync_caption()
        self.update()
        if self.scene():
            self.scene().set_dirty(True)

    # -------------------------------------------------------------------------
    # PAINT
    # -------------------------------------------------------------------------

    def paint_content(self, painter):
        """
        Render the pixmap scaled into the padded image area.
        The image is clipped to a rounded rect matching the node's corner radius,
        giving it the same beveled-frame appearance as the node shell itself.
        Aspect ratio is preserved — letterboxed within the padded rect.
        Shows a placeholder hint when no image is loaded.
        """
        image_rect = self._image_rect()

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                int(image_rect.width()),
                int(image_rect.height()),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # Center within the padded rect
            x_offset = image_rect.x() + (image_rect.width()  - scaled.width())  / 2
            y_offset = image_rect.y() + (image_rect.height() - scaled.height()) / 2

            # Clip to a rounded rect so the image corners match the node shell.
            # The clip radius is slightly smaller than the node's own round_radius
            # to account for the IMAGE_PADDING inset — keeps the curve visually consistent.
            clip_path = QPainterPath()
            clip_radius = max(2.0, self.round_radius - self.IMAGE_PADDING)
            clip_path.addRoundedRect(
                QRectF(x_offset, y_offset, scaled.width(), scaled.height()),
                clip_radius, clip_radius
            )
            painter.setClipPath(clip_path)
            painter.drawPixmap(int(x_offset), int(y_offset), scaled)
            painter.save()
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                QRectF(x_offset, y_offset, scaled.width(), scaled.height()),
                clip_radius, clip_radius
            )
            painter.restore()
        else:
            painter.save()
            painter.setOpacity(0.3)
            painter.setFont(QFont(Theme.buttonFontFamily, 9))
            painter.setPen(Theme.imageCaptionColor)
            painter.drawText(image_rect, Qt.AlignCenter, "double-click to load image")
            painter.restore()

    def shape(self):
        """Precise rounded rect shape for click detection."""
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.round_radius, self.round_radius)
        return path

    # -------------------------------------------------------------------------
    # RESIZE — keep caption in sync
    # -------------------------------------------------------------------------

    def setRect(self, rect: QRectF):
        """Sync caption position whenever the node rect changes."""
        super().setRect(rect)
        if hasattr(self, '_caption_item') and self._caption_item:
            self._sync_caption()

    def mouseMoveEvent(self, event):
        """Sync caption during live resize drag."""
        if self._is_resizing:
            self._sync_caption()
        super().mouseMoveEvent(event)

    # -------------------------------------------------------------------------
    # DOUBLE CLICK — image area opens browser, caption area enters edit mode
    # -------------------------------------------------------------------------

    def mouseDoubleClickEvent(self, event):
        """
        Route double-click by zone:
          Caption band  → inline title edit
          Image area    → file browser to load image
        """
        if event.button() == Qt.MouseButton.LeftButton:
            caption_top = self.rect().height() - self.CAPTION_HEIGHT

            if event.pos().y() >= caption_top:
                self._start_caption_edit()
            else:
                path, _ = QFileDialog.getOpenFileName(
                    None, "Select Image", "",
                    "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
                )
                if path:
                    self.load_from_path(path)
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Commit on Enter, cancel on Escape during caption edit."""
        if self._is_editing_caption:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._commit_caption_edit()
                event.accept()
                return
            if event.key() == Qt.Key_Escape:
                self._is_editing_caption = False
                self._caption_item.setTextInteractionFlags(Qt.NoTextInteraction)
                self._caption_item.clearFocus()
                if self.scene() and self.scene().views():
                    self.scene().views()[0].setFocusPolicy(Qt.NoFocus)
                self._sync_caption()
                event.accept()
                return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        """Commit any in-progress caption edit when the node loses focus."""
        if self._is_editing_caption:
            self._commit_caption_edit()
        super().focusOutEvent(event)

    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------

    def _prepare_for_removal(self):
        """
        Release pixmap and child item references before BaseNode teardown.
        Subclass cleans its own children first — same teardown order as WarmNode.
        """
        self._pixmap = None
        if self._caption_item:
            self._caption_item.setParentItem(None)
            self._caption_item = None
        self._is_editing_caption = False
        super()._prepare_for_removal()

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Extend base serialization with image data as base64 PNG.
        Session is fully self-contained — no external file references.
        """
        data = super().to_dict()

        if self._pixmap and not self._pixmap.isNull():
            from PySide6.QtCore import QByteArray, QBuffer, QIODevice
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            self._pixmap.save(buffer, "PNG")
            buffer.close()
            data["image_b64"] = base64.b64encode(bytes(byte_array)).decode("utf-8")
        else:
            data["image_b64"] = None

        return data

    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        """Deserialize an ImageNode from session data."""
        node = ImageNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", ""),
            pos=QPointF(data.get("pos_x", 0.0), data.get("pos_y", 0.0)),
            width=float(data.get("width", 260.0)),
            height=float(data.get("height", 220.0)),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)

        b64 = data.get("image_b64")
        if b64:
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(b64))
            if not pixmap.isNull():
                node._pixmap = pixmap

        node._sync_caption()
        return node
