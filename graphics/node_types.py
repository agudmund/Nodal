#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node_types.py specialized node implementations
-Type-specific node classes with resizable rects, ports, animations, and custom rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid as _uuid
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsDropShadowEffect, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QSizeF, QAbstractAnimation
from PySide6.QtGui import QColor, QPen, QFont, QPainter, QBrush
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
        self.node_type = "node"  # Override in subclasses

        # Resize handling
        self._resize_handle_size = 12
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_rect = QRectF()

        # Drag tracking for proper invalidation
        self._last_scene_pos = pos

        # Port management
        self.ports_visible = False
        self.input_port = None
        self.output_port = None
        self._port_anim = None
        self._create_ports()

        # Hover animation (smooth scale pulse with variable duration per node)
        self.pulse_anim = QVariantAnimation()
        pulse_duration = random.randint(400, 600)
        self.pulse_anim.setDuration(pulse_duration)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(1.025)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pulse_anim.valueChanged.connect(self.setScale)

        # Pen colors for hover
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

        # Visuals - Centralizing the "Cozy" look
        self.setBrush(QColor(30, 30, 30, 200))
        self.round_radius = 18

        # Set initial pen
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
        """
        Handle item changes like position, selection, visibility.
        Ensures the scene properly invalidates both old and new regions during drag.
        """
        if change == QGraphicsRectItem.ItemPositionChange:
            # BEFORE position changes: invalidate the OLD position
            if self.scene() and self._last_scene_pos != value:
                # Calculate the bounding rect at the OLD position
                old_rect = self.rect().translated(self._last_scene_pos)
                shadow_margin = 22
                old_bounds = old_rect.adjusted(-shadow_margin, -shadow_margin, shadow_margin, shadow_margin)
                self.scene().update(old_bounds)

        elif change == QGraphicsRectItem.ItemPositionHasChanged:
            # AFTER position changed: invalidate the NEW position
            if self.scene():
                self._last_scene_pos = self.scenePos()
                # Invalidate new position (includes shadow margins)
                self.scene().update(self.sceneBoundingRect())

        return super().itemChange(change, value)

    def _update_port_positions(self):
        """Update port positions to be outside the node, centered vertically on rect center."""
        rect = self.rect()
        # Center the ports vertically on the rect's midpoint
        center_y = int(rect.height() - 25)

        # Input port on the left, outside the node
        self.input_port.setPos(-3, center_y)

        # Output port on the right, outside the node
        self.output_port.setPos(int(rect.width()) + 3, center_y)

    def toggle_ports(self):
        """Toggle port visibility with smooth fade animation."""
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
        """
        Handle double-click events:
        - Double LEFT-click: open note editor
        - Double RIGHT-click: toggle ports visibility
        """
        if event.button() == Qt.LeftButton:
            # Open the note editor for this node
            self.open_editor()
        elif event.button() == Qt.RightButton:
            # Toggle ports on double right-click
            self.toggle_ports()

        super().mouseDoubleClickEvent(event)

    def open_editor(self):
        """Open the note editor for this node. Placeholder implementation."""
        # Create a simple placeholder dialog
        dialog = QDialog()
        dialog.setWindowTitle(f"Edit Node: {self.title}")
        dialog.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        label = QLabel(f"Note Editor Placeholder\n\nNode: {self.title}\nUUID: {self.uuid}")
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec()

    def mousePressEvent(self, event):
        """Check if resize handle was clicked."""
        if event.button() == Qt.LeftButton:
            # Check if click is near the bottom-right corner (resize handle area)
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

        # Calculate new dimensions
        delta = event.pos() - self._resize_start_pos
        new_width = max(120, self._resize_start_rect.width() + delta.x())
        new_height = max(50, self._resize_start_rect.height() + delta.y())

        # Optional: hold Shift to maintain aspect ratio
        if event.modifiers() & Qt.ShiftModifier:
            orig_ratio = self._resize_start_rect.width() / self._resize_start_rect.height()
            new_height = new_width / orig_ratio

        # Update the node size
        self.prepareGeometryChange()
        self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, new_height)))

        # Explicitly invalidate the scene region including shadow margins
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
        # Draw the main body
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), self.round_radius, self.round_radius)

        # Draw resize handle in bottom-right corner (diagonal lines)
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
        br = self.rect().bottomRight()
        for i in range(3):
            offset = (i + 1) * 4
            painter.drawLine(br.x() - offset, br.y() - 2, br.x() - 2, br.y() - offset)

        # Only show body content if there's enough vertical space
        if self.rect().height() >= 60:
            # Let subclasses draw their specific content
            self.paint_content(painter)

    def setRect(self, rect):
        """Override to update port positions when node is resized."""
        super().setRect(rect)
        self._update_port_positions()

    def boundingRect(self):
        """
        Return the full rect including shadow effect margins.
        The drop shadow extends ~20 pixels beyond the rect (blur radius 15 + offset 5).
        """
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

        # Dispatch to correct node class based on type
        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        else:
            # Default fallback to base node
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
    """Text/thought node - displays title and full text content with word wrapping."""

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
        # Use provided dimensions or fall back to defaults
        if width is None:
            width = Theme.NODE_WIDTH
        if height is None:
            height = Theme.NODE_HEIGHT

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "warm"
        self.setBrush(QColor(30, 30, 30, 200))

    def paint_content(self, painter):
        """Render title and full text with proper wrapping and layout."""
        padding = 12
        inner_width = self.rect().width() - (padding * 2)
        inner_height = self.rect().height() - (padding * 2)

        if inner_width <= 0 or inner_height <= 0:
            return

        # Render title (bold, larger font)
        title_font = QFont(Theme.BUTTON_FONT_FAMILY, 11, QFont.Bold)
        painter.setFont(title_font)

        # Title shadow
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(padding + 1, padding + 1, inner_width, inner_height, 
                        Qt.TextWordWrap | Qt.AlignTop, self.title)

        # Title main color
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.drawText(padding, padding, inner_width, inner_height, 
                        Qt.TextWordWrap | Qt.AlignTop, self.title)

        # Calculate space for title
        title_rect = painter.fontMetrics().boundingRect(
            padding, padding, inner_width, inner_height,
            Qt.TextWordWrap | Qt.AlignTop, self.title
        )
        title_height = title_rect.height() + 8

        # Render full text if available
        if self.full_text and self.full_text.strip():
            body_font = QFont(Theme.BUTTON_FONT_FAMILY, 9, QFont.Normal)
            painter.setFont(body_font)
            painter.setPen(QColor(200, 200, 200, 210))

            text_rect_height = inner_height - title_height
            if text_rect_height > 5:
                painter.drawText(padding, padding + title_height, inner_width, 
                               text_rect_height, Qt.TextWordWrap | Qt.AlignTop, 
                               self.full_text)

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
        # Darker, more muted styling
        self.setBrush(QColor(40, 40, 50, 200))

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
        self.image = None  # Will load actual image later if available

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
