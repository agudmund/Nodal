#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - BaseNode.py base node graphics item
-Foundation class for all node types: ports, connections, resize, hover, serialization
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid as _uuid
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QSizeF, QAbstractAnimation, QTimer
from PySide6.QtGui import QColor, QPen, QPainter, QBrush, QPainterPath
from .theme import Theme
from .port import Port
from utils.logger import setup_logger

logger = setup_logger()


class BaseNode(QGraphicsRectItem):
    """
    Foundation class for all node types.
    Provides core functionality: input/output ports, connections, interactive resize,
    hover animations with pulse effect, and serialization for session persistence.

    Subclasses override paint_content() to draw type-specific visuals.
    Subclasses can override mouseDoubleClickEvent() for custom double-click behavior.
    """

    def __init__(self, node_id, title, full_text, pos=QPointF(0, 0), width=300, height=200, uuid=None):
        """
        Initialize a BaseNode with identification, positioning, and visual properties.

        Args:
            node_id: Unique identifier for this node in the scene
            title: Node title/label text
            full_text: Extended content text for node-specific rendering
            pos: Scene position as QPointF (default: origin)
            width: Node width in pixels (default: 300)
            height: Node height in pixels (default: 200)
            uuid: Unique identifier for serialization (auto-generated if None)
        """
        super().__init__(0, 0, width, height)

        self.ports_visible = False
        self.connections = []

        # Look at the ledger and manifest the ports if needed
        QTimer.singleShot(0, self._sync_port_visibility)

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
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
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

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)

        self.setTransformOriginPoint(self.rect().center())

    # -------------------------------------------------------------------------
    # KINEMATICS
    # -------------------------------------------------------------------------

    def itemChange(self, change, value):
        """THE CENTRAL NERVE HUB — wire updates, dirty flags, IK kinematics."""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self, 'connections'):
                for conn in self.connections:
                    conn.update_path()
            self._last_scene_pos = self.scenePos()
            if self.scene():
                self.scene().set_dirty(True)
        return super().itemChange(change, value)

    # -------------------------------------------------------------------------
    # PORTS
    # -------------------------------------------------------------------------

    def _create_ports(self):
        """Create input and output ports, hidden initially."""
        self.input_port = Port(self, is_output=False)
        self.output_port = Port(self, is_output=True)
        self._update_port_positions()
        self.input_port.hide()
        self.output_port.hide()

    def _update_port_positions(self):
        """Position ports outside the node edges, centered vertically."""
        rect = self.rect()
        center_y = int(rect.height() - 25)
        self.input_port.setPos(-3, center_y)
        self.output_port.setPos(int(rect.width()) + 3, center_y)

    def toggle_ports(self):
        """Toggle port visibility."""
        self.ports_visible = not self.ports_visible
        self._animate_ports()

    def _animate_ports(self):
        """Fade ports in/out."""
        if self._port_anim and self._port_anim.state() == QAbstractAnimation.Running:
            self._port_anim.stop()
        if self.ports_visible:
            self.input_port.show()
            self.output_port.show()
        else:
            self.input_port.hide()
            self.output_port.hide()

    def _sync_port_visibility(self):
        """Rebuild ports based on current visibility state and connection ledger."""
        # Clear existing ports
        existing_ports = [item for item in self.childItems() if isinstance(item, Port)]
        for p in existing_ports:
            if self.scene():
                self.scene().removeItem(p)

        if self.ports_visible:
            # Output (Mint) — always visible if toggled
            self.output_port = Port(self, is_output=True)
            self.output_port.setPos(self.rect().width(), self.rect().height() / 2)

            # Input (Copper) — only visible if a nerve is attached
            has_incoming = any(c.end_node == self for c in self.connections)
            if has_incoming:
                self.input_port = Port(self, is_output=False)
                self.input_port.setPos(0, self.rect().height() / 2)


    # -------------------------------------------------------------------------
    # MOUSE EVENTS
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 1. PORT HANDSHAKE
            click_pos = event.scenePos()
            for child in self.childItems():
                if isinstance(child, Port):
                    if child.contains(child.mapFromScene(click_pos)):
                        if getattr(child, 'is_output', False):
                            from .connection import Connection
                            self.temp_connection = Connection(self)
                            self.scene().addItem(self.temp_connection)
                            event.accept()
                            return

            # 2. RESIZE HANDLE
            rect = self.rect()
            handle_area = QRectF(rect.right() - 20, rect.bottom() - 20, 20, 20)
            if handle_area.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self._resize_start_rect = self.rect()
                event.accept()
                return

        # 3. FALLBACK: Standard drag
        self._is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Live wire follow and resize stretch."""
        if hasattr(self, 'temp_connection') and self.temp_connection:
            self.temp_connection.update_path(event.scenePos())
            event.accept()
            return

        super().mouseMoveEvent(event)

        if self._is_resizing:
            delta = event.pos() - self._resize_start_pos
            new_width = max(120, self._resize_start_rect.width() + delta.x())
            new_height = max(50, self._resize_start_rect.height() + delta.y())

            if event.modifiers() & Qt.ShiftModifier:
                ratio = self._resize_start_rect.width() / self._resize_start_rect.height()
                new_height = new_width / ratio

            self.prepareGeometryChange()
            self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, new_height)))
            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finalise connection or resize."""
        if self._is_resizing:
            self._is_resizing = False
            self._sync_port_visibility()
            event.accept()

        if hasattr(self, 'temp_connection') and self.temp_connection:
            items = self.scene().items(event.scenePos())
            target_node = None
            for item in items:
                if isinstance(item, BaseNode) and item != self:
                    target_node = item
                    break

            if target_node:
                self.temp_connection.end_node = target_node
                if self.temp_connection not in self.connections:
                    self.connections.append(self.temp_connection)
                if hasattr(target_node, 'connections') and self.temp_connection not in target_node.connections:
                    target_node.connections.append(self.temp_connection)
                target_node._sync_port_visibility()
                self.temp_connection.update_path()
                if self.scene():
                    self.scene().set_dirty(True)
            else:
                self.scene().removeItem(self.temp_connection)

            self.temp_connection = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Left double-click opens editor, right double-click toggles ports."""
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "open_editor"):
                self.open_editor()
                event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.ports_visible = not self.ports_visible
            if self.scene():
                self.scene().set_dirty(True)
            self._sync_port_visibility()
            event.accept()

    # -------------------------------------------------------------------------
    # HOVER
    # -------------------------------------------------------------------------

    def hoverEnterEvent(self, event):
        """Gentle pulse animation on hover."""
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

    # -------------------------------------------------------------------------
    # PAINT PIPELINE
    # -------------------------------------------------------------------------

    def paint(self, painter, option, widget):
        """
        THE UNIFIED PAINT PIPELINE
        Shell → Glow → LOD gate → Resize handle → Specialist handoff
        """
        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        rect = self.rect()

        # 1. BODY
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setPen(QPen(QColor("#a8d0ff"), 2.5, Qt.SolidLine))
        else:
            painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, self.round_radius, self.round_radius)

        # 2. LOD GATE
        if lod < 0.3:
            for child in self.childItems():
                if not isinstance(child, Port):
                    child.hide()
                else:
                    child.setGraphicsEffect(None)
            if self.graphicsEffect():
                self.graphicsEffect().setEnabled(False)
            return

        # 3. RESIZE HANDLE (The Triangle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        handle_path = QPainterPath()
        handle_path.moveTo(rect.right(), rect.bottom() - 12)
        handle_path.lineTo(rect.right(), rect.bottom())
        handle_path.lineTo(rect.right() - 12, rect.bottom())
        handle_path.closeSubpath()
        painter.drawPath(handle_path)

        # 4. SPECIALIST HANDOFF
        self.paint_content(painter)

    def paint_content(self, painter):
        """Override in subclasses to draw type-specific content."""
        pass

    # -------------------------------------------------------------------------
    # GEOMETRY
    # -------------------------------------------------------------------------

    def setRect(self, rect):
        """Sync port positions when node is resized."""
        super().setRect(rect)
        self._update_port_positions()

    def boundingRect(self):
        """Include shadow margins in bounding rect."""
        shadow_margin = 22
        return self.rect().adjusted(-shadow_margin, -shadow_margin, shadow_margin, shadow_margin)

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self):
        """Serialize node state to dictionary for session persistence."""
        return {
            "node_id": self.node_id,
            "uuid": self.uuid,
            "type": self.node_type,
            "title": self.title,
            "full_text": self.full_text,
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "width": self.rect().width(),
            "height": self.rect().height(),
            "ports_visible": self.ports_visible,
        }

    @staticmethod
    def from_dict(data: dict) -> 'BaseNode':
        """
        Factory method - routes to correct subclass based on node type.
        Uses local imports to avoid circular dependency issues.

        Args:
            data: Dictionary containing node state (must include 'type' key)

        Returns:
            Appropriate BaseNode subclass instance (WarmNode, ImageNode, AboutNode, or BaseNode)
        """
        from .node_types import WarmNode, ImageNode, AboutNode

        node_type = data.get("type", "node")

        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        else:
            return BaseNode._create_from_dict(data)

    @staticmethod
    def _create_from_dict(data: dict) -> 'BaseNode':
        """Fallback factory for creating generic BaseNode instances from serialized data."""
        node = BaseNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Node"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 300),
            height=data.get("height", 200),
            uuid=data.get("uuid")
        );
        node.ports_visible = data.get("ports_visible", False)
        return node