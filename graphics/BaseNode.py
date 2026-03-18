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
from .Theme import Theme
from .Port import Port
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

    def __init__(self, node_id: int, title: str, pos: QPointF = QPointF(0, 0), 
             width: float = 300.0, height: float = 200.0, uuid: str = None):
        """
        Initialize a BaseNode with identification, positioning, and visual properties.

        Args:
            node_id: Unique identifier for this node in the scene
            title: Node title/label text
            pos: Scene position as QPointF (default: origin)
            width: Node width in pixels (default: 300)
            height: Node height in pixels (default: 200)
            uuid: Unique identifier for serialization (auto-generated if None)
        """
        super().__init__(0, 0, width, height)

        self.ports_visible = False
        self.connections = []

        # Throttle itemChange updates to prevent excessive connection redraws
        self._update_throttle_timer = None
        self._pending_update = False

        self.setPos(pos)

        # Identification
        self.node_id = node_id
        self.title = title
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
        pulse_duration = random.randint(Theme.nodePulseMin, Theme.nodePulseMax)
        self.pulse_anim.setDuration(pulse_duration)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(Theme.nodePulseScale)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pulse_anim.valueChanged.connect(self.setScale)

        # Pen styling
        self.normal_pen = QPen(Theme.primaryBorder, Theme.nodeBorderWidth)
        self.hover_pen = QPen(Theme.lighten(Theme.primaryBorder), Theme.nodeBorderWidth)
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
        self.setBrush(Theme.nodeDefaultBg)
        self.round_radius = Theme.nodeRoundRadius
        self.setPen(self.current_pen)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(Theme.nodeShadowBlur)
        shadow.setColor(Theme.nodeShadowColor)
        shadow.setOffset(Theme.nodeShadowOffsetX, Theme.nodeShadowOffsetY)
        self.setGraphicsEffect(shadow)

        self.setTransformOriginPoint(self.rect().center())

        # Cache paint objects to avoid recreating every frame
        self._selected_pen = QPen(Theme.textPrimary, Theme.nodeBorderWidth * Theme.nodeBorderSelectedScale, Qt.SolidLine)

    # -------------------------------------------------------------------------
    # KINEMATICS
    # -------------------------------------------------------------------------

    def itemChange(self, change, value):
        """Throttled update handler for node position changes to prevent excessive redraws."""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            self._last_scene_pos = self.scenePos()
            # Throttle connection updates - batch them together
            self._pending_update = True
            if not self._update_throttle_timer:
                self._update_throttle_timer = QTimer()
                self._update_throttle_timer.setSingleShot(True)
                self._update_throttle_timer.timeout.connect(self._execute_pending_update)
                self._update_throttle_timer.start(Theme.nodeUpdateThrottle)
        return super().itemChange(change, value)

    def _execute_pending_update(self):
        """Execute batched connection updates after throttle period."""
        if self._pending_update and hasattr(self, 'connections'):
            for conn in self.connections:
                conn.update_path()
            if self.scene():
                self.scene().set_dirty(True)
            self._pending_update = False
        self._update_throttle_timer = None

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
        center_y = int(rect.height() + Theme.portVerticalOffset)
        self.input_port.setPos(-Theme.portHorizontalNudge, center_y)
        self.output_port.setPos(int(rect.width()) + Theme.portHorizontalNudge, center_y)

    def toggle_ports(self):
        """Toggle port visibility."""
        self.ports_visible = not self.ports_visible
        self._animate_ports()

    def _animate_ports(self):
        """Toggle port visibility with optional animation."""
        if self._port_anim and self._port_anim.state() == QAbstractAnimation.Running:
            self._port_anim.stop()
        # Simply show/hide ports instead of recreating them
        if self.input_port:
            self.input_port.setVisible(self.ports_visible)
        if self.output_port:
            self.output_port.setVisible(self.ports_visible)

    def _sync_port_visibility(self):
        """Sync port visibility states with current configuration."""
        # Ports are already created in _create_ports() - just manage visibility
        if self.input_port:
            self.input_port.setVisible(self.ports_visible)
        if self.output_port:
            self.output_port.setVisible(self.ports_visible)


    # -------------------------------------------------------------------------
    # MOUSE EVENTS
    # -------------------------------------------------------------------------

    def on_port_clicked(self, port, event):
        """Called directly by Port.mousePressEvent — start a wire from the output port."""
        port_type = 'OUTPUT' if port.is_output else 'INPUT'
        logger.debug(f"[NODE] on_port_clicked — port={port_type} node={self.title}")
        if port.is_output:
            from .Connection import Connection
            self.temp_connection = Connection(self)
            self.scene().addItem(self.temp_connection)
            logger.debug(f"[NODE] Wire started from output port of '{self.title}'")
        else:
            logger.debug(f"[NODE] INPUT port clicked — no wire start action")

    def mousePressEvent(self, event):
        logger.debug(f"[NODE] mousePressEvent — button={event.button()} scenePos={event.scenePos()} node='{self.title}'")
        if event.button() == Qt.LeftButton:
            # 1. PORT HANDSHAKE (fallback — should now be handled by Port.mousePressEvent directly)
            click_pos = event.scenePos()
            for child in self.childItems():
                if isinstance(child, Port):
                    mapped = child.mapFromScene(click_pos)
                    hit = child.contains(mapped)
                    logger.debug(f"[NODE]   child port is_output={child.is_output} visible={child.isVisible()} mapped={mapped} contains={hit}")
                    if hit:
                        if getattr(child, 'is_output', False):
                            from .Connection import Connection
                            self.temp_connection = Connection(self)
                            self.scene().addItem(self.temp_connection)
                            logger.debug(f"[NODE]   Wire started via fallback path")
                            event.accept()
                            return

            # 2. RESIZE HANDLE
            rect = self.rect()
            handle_area = QRectF(rect.right() - 20, rect.bottom() - 20, 20, 20)
            if handle_area.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self._resize_start_rect = self.rect()
                logger.debug(f"[NODE]   Resize handle activated")
                event.accept()
                return

        # 3. FALLBACK: Standard drag
        logger.debug(f"[NODE]   Falling through to drag")
        self._is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Live wire follow and resize stretch."""
        if hasattr(self, 'temp_connection') and self.temp_connection:
            self.temp_connection.update_path(event.scenePos())
            event.accept()
            return

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
        THE UNIFIED PAINT PIPELINE - optimized to reuse cached objects.
        Shell → Glow → LOD gate → Resize handle → Specialist handoff
        """
        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        rect = self.rect()

        # 1. BODY
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setPen(self._selected_pen)  # Use cached pen
        else:
            painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, self.round_radius, self.round_radius)

        # 2. LOD GATE - only process at detail levels that matter
        if lod < Theme.nodeLodThreshold:
            # At very low LOD, hide details
            if self.graphicsEffect():
                self.graphicsEffect().setEnabled(False)
            return

        # Re-enable graphics effect at normal LOD
        if self.graphicsEffect():
            self.graphicsEffect().setEnabled(True)

        # 3. CORNER TAPER — resize grip, isolated for future asset replacement
        self._draw_corner_taper(painter)

        # 4. SPECIALIST HANDOFF
        self.paint_content(painter)

    def _draw_corner_taper(self, painter):
        """Resize grip — swap Theme.resizeGripImage for any asset anytime."""
        pixmap = Theme.getResizeGripPixmap()
        if pixmap and not pixmap.isNull():
            br = self.rect().bottomRight()
            painter.drawPixmap(
                int(br.x()) - pixmap.width(),
                int(br.y()) - pixmap.height(),
                pixmap
            )

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
        return self.rect().adjusted(-Theme.nodeShadowMargin, -Theme.nodeShadowMargin, Theme.nodeShadowMargin, Theme.nodeShadowMargin)

    def shape(self):
        """Match hit-test shape to boundingRect so port clicks reach mousePressEvent."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

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
        from .WarmNode import WarmNode
        from .ImageNode import ImageNode
        from .AboutNode import AboutNode

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
            pos=QPointF(data.get("pos_x", 0.0), data.get("pos_y", 0.0)),
            width=float(data.get("width", 300.0)),
            height=float(data.get("height", 200.0)),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node