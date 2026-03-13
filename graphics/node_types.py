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
from PySide6.QtGui import QColor, QPen, QFont, QPainter, QBrush, QFontMetrics, QTextDocument
from utils.theme import Theme
from graphics.port import Port


class NodeBase(QGraphicsRectItem):
    """Base class for all node types with resize, ports, animations, and rich rendering."""

    def __init__(self, node_id, title, full_text, pos=QPointF(0, 0), width=300, height=200, uuid=None):
        super().__init__(0, 0, width, height)
        self.setPos(pos)

        # Identification
        self.node_id = node_id
        self.title = title
        self.full_text = full_text
        self.uuid = uuid or _uuid.uuid4().hex
        self.node_type = "node"

        # Resize handling
        self._resize_handle_size = 12
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_rect = QRectF()

        # Drag tracking
        self._last_scene_pos = pos

        # Port management
        self.ports_visible = False
        self.input_port = None
        self.output_port = None
        self._port_anim = None
        self._create_ports()

        # Hover animation
        self.pulse_anim = QVariantAnimation()
        pulse_duration = random.randint(400, 600)
        self.pulse_anim.setDuration(pulse_duration)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(1.025)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pulse_anim.valueChanged.connect(self.setScale)

        # Pen styling
        self.normal_pen = QPen(QColor("#444444"), 2)
        self.hover_pen = QPen(self.normal_pen.color().lighter(125), 2)
        self.current_pen = self.normal_pen

        # UI State
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | 
            QGraphicsRectItem.ItemIsSelectable | 
            QGraphicsRectItem.ItemSendsGeometryChanges |
            QGraphicsRectItem.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        # Visuals
        self.setBrush(QColor(30, 30, 30, 200))
        self.round_radius = 18
        self.setPen(self.current_pen)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)

        self.setTransformOriginPoint(self.rect().center())

    def _create_ports(self):
        """Create input and output ports but keep them hidden initially."""
        self.input_port = Port(self, is_output=False)
        self.output_port = Port(self, is_output=True)
        self._update_port_positions()
        self.input_port.hide()
        self.output_port.hide()

    def itemChange(self, change, value):
        """Handle item changes like position, selection, visibility."""
        if change == QGraphicsRectItem.ItemPositionChange:
            if self.scene() and self._last_scene_pos != value:
                old_rect = self.rect().translated(self._last_scene_pos)
                shadow_margin = 22
                old_bounds = old_rect.adjusted(-shadow_margin, -shadow_margin, shadow_margin, shadow_margin)
                self.scene().update(old_bounds)

        elif change == QGraphicsRectItem.ItemPositionHasChanged:
            if self.scene():
                self._last_scene_pos = self.scenePos()
                self.scene().update(self.sceneBoundingRect())

        return super().itemChange(change, value)

    def _update_port_positions(self):
        """Update port positions to be outside the node, centered vertically."""
        rect = self.rect()
        center_y = int(rect.height() - 25)
        self.input_port.setPos(-3, center_y)
        self.output_port.setPos(int(rect.width()) + 3, center_y)

    def toggle_ports(self):
        """Toggle port visibility."""
        self.ports_visible = not self.ports_visible
        self._animate_ports()

    def _animate_ports(self):
        """Smoothly fade ports in/out."""
        if self._port_anim and self._port_anim.state() == QAbstractAnimation.Running:
            self._port_anim.stop()

        if self.ports_visible:
            self.input_port.show()
            self.output_port.show()
        else:
            self.input_port.hide()
            self.output_port.hide()

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events."""
        if event.button() == Qt.LeftButton:
            self.open_editor()
        elif event.button() == Qt.RightButton:
            self.toggle_ports()
        super().mouseDoubleClickEvent(event)

    def open_editor(self):
        """Open the note editor for this node. Override in subclasses."""
        pass

    def mousePressEvent(self, event):
        """Check if resize handle was clicked."""
        if event.button() == Qt.LeftButton:
            rect = self.rect()
            handle_area = QRectF(
                rect.right() - self._resize_handle_size * 2,
                rect.bottom() - self._resize_handle_size * 2,
                self._resize_handle_size * 2,
                self._resize_handle_size * 2
            )
            if handle_area.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self._resize_start_rect = self.rect()
                event.accept()
                return

        self._is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle node dragging and resizing."""
        if not self._is_resizing:
            return super().mouseMoveEvent(event)

        delta = event.pos() - self._resize_start_pos
        new_width = max(120, self._resize_start_rect.width() + delta.x())
        new_height = max(50, self._resize_start_rect.height() + delta.y())

        if event.modifiers() & Qt.ShiftModifier:
            orig_ratio = self._resize_start_rect.width() / self._resize_start_rect.height()
            new_height = new_width / orig_ratio

        self.prepareGeometryChange()
        self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, new_height)))

        if self.scene():
            self.scene().update(self.sceneBoundingRect())

        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        """Stop resizing."""
        if self._is_resizing:
            self._is_resizing = False
            event.accept()
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        """Trigger a gentle pulse animation on hover."""
        self.current_pen = self.hover_pen
        self.setPen(self.current_pen)
        self.update()

        if self.pulse_anim.state() == QVariantAnimation.Stopped:
            self.pulse_anim.setDirection(QVariantAnimation.Forward)
            self.pulse_anim.start()

            def reverse_pulse():
                if self.pulse_anim.direction() == QVariantAnimation.Forward:
                    self.pulse_anim.setDirection(QVariantAnimation.Backward)
                    self.pulse_anim.start()

            if self.pulse_anim.receivers("finished") > 0:
                self.pulse_anim.finished.disconnect()
            self.pulse_anim.finished.connect(reverse_pulse)

        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Reset pen on hover leave."""
        self.current_pen = self.normal_pen
        self.setPen(self.current_pen)
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget):
        """Paint the node body and delegate content to subclasses."""
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), self.round_radius, self.round_radius)

        # Draw resize handle in bottom-right corner
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
        br = self.rect().bottomRight()
        for i in range(3):
            offset = (i + 1) * 4
            painter.drawLine(br.x() - offset, br.y() - 2, br.x() - 2, br.y() - offset)

        if self.rect().height() >= 60:
            self.paint_content(painter)

    def setRect(self, rect):
        """Override to update port positions when node is resized."""
        super().setRect(rect)
        self._update_port_positions()

    def boundingRect(self):
        """Return the full rect including shadow effect margins."""
        shadow_margin = 22
        rect = self.rect()
        return rect.adjusted(-shadow_margin, -shadow_margin, shadow_margin, shadow_margin)

    def paint_content(self, painter):
        """Override this in subclasses to draw text, images, or renders."""
        pass

    def to_dict(self):
        """Standardized export for SessionManager."""
        return {
            "node_id": self.node_id,
            "uuid": self.uuid,
            "type": self.node_type,
            "title": self.title,
            "full_text": self.full_text,
            "pos_x": self.scenePos().x(),
            "pos_y": self.scenePos().y(),
            "width": self.rect().width(),
            "height": self.rect().height(),
            "ports_visible": self.ports_visible
        }

    @staticmethod
    def from_dict(data: dict) -> 'NodeBase':
        """Factory method to create appropriate node type from dictionary."""
        node_type = data.get("type", "node")

        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        else:
            return NodeBase._create_from_dict(data)

    @staticmethod
    def _create_from_dict(data: dict) -> 'NodeBase':
        """Create base node from dict."""
        node = NodeBase(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Node"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 300),
            height=data.get("height", 200),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class WarmNode(NodeBase):
    """Text/thought node with QGraphicsTextItem, emoji, and note editor."""

    MIN_WIDTH = 180
    MIN_HEIGHT = 60
    MAX_HEIGHT = 1000
    MARGIN = 20

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
        if width is None:
            width = Theme.NODE_WIDTH
        if height is None:
            height = Theme.NODE_HEIGHT

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "warm"
        self.setBrush(Theme.WARM_NODE_BG)

        # Random emoji for visual personality
        self.emoji = random.choice(["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"])

        # QGraphicsTextItem for emoji
        self.emoji_item = QGraphicsTextItem(self)
        self.emoji_item.setFont(QFont("Segoe UI Emoji", 28))
        self.emoji_item.setPlainText(self.emoji)
        self.emoji_item.setPos(5, 3)

        # QGraphicsTextItem for title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setFont(QFont(Theme.NODE_TITLE_FONT_FAMILY, Theme.NODE_TITLE_FONT_SIZE, QFont.Bold))
        self.title_item.setDefaultTextColor(QColor("#a8d0ff"))

        # QGraphicsTextItem for body text
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont(Theme.NODE_BODY_FONT_FAMILY, Theme.NODE_BODY_FONT_SIZE))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))

        # Layout update timer
        self._layout_timer = QTimer()
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._sync_content_layout)

        # Track if editor is open
        self._editor = None

        self._sync_content_layout()

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

        # Get the main window to set window priority
        main_window = None
        for view in self.scene().views():
            main_window = view.window()
            break

        # Create editor dialog
        self._editor = CozyNoteEditor(self.node_id, self.title, self.full_text, parent=main_window)

        # Set note editor to be on top while main window loses that flag
        if main_window:
            self._editor.setWindowFlags(self._editor.windowFlags() | Qt.WindowStaysOnTopHint)
            # Remove always-on-top from main window
            main_window.setWindowFlags(main_window.windowFlags() & ~Qt.WindowStaysOnTopHint)
            main_window.show()

        # Connect signals
        self._editor.accepted.connect(self._on_editor_accepted)
        self._editor.rejected.connect(self._on_editor_rejected)

        # Show modeless dialog
        self._editor.setModal(False)
        self._editor.show()

    def _on_editor_accepted(self):
        """User clicked Save → apply changes."""
        if self._editor:
            self.title = self._editor.get_title()
            self.full_text = self._editor.get_text()
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
        """Clean up editor and restore main window priority."""
        if self._editor:
            # Restore main window always-on-top flag
            main_window = self._editor.parent()
            if main_window:
                main_window.setWindowFlags(main_window.windowFlags() | Qt.WindowStaysOnTopHint)
                main_window.show()

            del self._editor
            self._editor = None

    @staticmethod
    def from_dict(data: dict) -> 'WarmNode':
        """Create WarmNode from dictionary."""
        node = WarmNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", ""),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class AboutNode(NodeBase):
    """Meta/information node - smaller, no ports."""

    def __init__(self, node_id=0, title="About", full_text="", pos=QPointF(0, 0), 
                 width=200, height=55, uuid=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "about"
        self.setBrush(Theme.ABOUT_NODE_BG)

    def paint_content(self, painter):
        """Simple text rendering for about nodes."""
        padding = 8
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 10, QFont.Bold))
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


class ImageNode(NodeBase):
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
        """Image nodes: show title as caption if needed."""
        if self.title and len(self.title) > 0:
            painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 8))
            painter.setPen(QColor(200, 200, 200, 150))
            painter.drawText(0, self.rect().height() - 15, self.rect().width(), 15, 
                           Qt.AlignCenter, self.title)

    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        """Create ImageNode from dictionary."""
        node = ImageNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", ""),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node
