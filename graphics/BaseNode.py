#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - BaseNode.py base node graphics item
-Foundation class for all node types: ports, connections, resize, hover, serialization for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid as _uuid
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QSizeF, QAbstractAnimation, QTimer
from PySide6.QtGui import QColor, QPen, QPainter, QBrush, QPainterPath
from .Theme import Theme
from .Port import Port
from utils.logger import setup_logger
from utils.NodeBehaviour import NodeBehaviour

logger = setup_logger()


class BaseNode(QGraphicsRectItem):
    """
    Foundation class for all node types in the nodal graph.

    Provides the shared core that every node type builds on: input and output ports,
    live wire connections, interactive corner resize, hover pulse animation, and
    session serialization. Subclasses are responsible only for their own visual
    content and any type-specific interaction — everything structural lives here.

    Subclassing contract:
        paint_content(painter)         — override to draw type-specific visuals inside the node body.
        mouseDoubleClickEvent(event)   — override to add custom double-click behaviour (e.g. opening an editor).
        to_dict() / from_dict(data)    — extend for any additional serialized state the subclass needs.

    Port behaviour:
        Ports are placed at the vertical center of the node on the left (input) and right (output) edges.
        Port vertical position is controlled by Theme.portVerticalOffset and updates automatically on resize.
        Port visibility is toggled via right double-click and persists through session save/load.

    Performance model:
        Position changes are throttled via _update_throttle_timer — connection redraws are batched
        rather than firing on every pixel of movement.
        Paint objects (pens) are cached at init to avoid per-frame allocation.
        LOD gating suppresses detail rendering when zoomed out past Theme.nodeLodThreshold.
    """

    def __init__(self, node_id: int, title: str, pos: QPointF = QPointF(0, 0),
                 width: float = 300.0, height: float = 200.0, uuid: str = None):
        """
        Initialize a BaseNode with identity, position, and visual setup.

        Args:
            node_id:  Integer identifier for this node within the scene.
                      Used for editor registry lookups and logging.
            title:    Display label for this node. Subclasses may derive or modify this.
            pos:      Initial scene position as QPointF. Defaults to origin.
            width:    Initial node width in pixels. Defaults to 300.
            height:   Initial node height in pixels. Defaults to 200.
            uuid:     Unique hex string for session serialization.
                      Auto-generated via uuid4 if not provided — only pass this
                      when restoring from a saved session.
        """
        super().__init__(0, 0, width, height)

        # ── Connection state ──────────────────────────────────────────────────
        self.ports_visible = False          # Whether ports are currently shown
        self.connections = []               # All Connection objects attached to this node
        self.temp_connection = None         # Active wire being drawn, cleared on mouse release

        # ── Position throttle ─────────────────────────────────────────────────
        # Connection redraws are batched behind a timer so rapid movement
        # doesn't flood the scene with individual update_path() calls.
        self._update_throttle_timer = None
        self._pending_update = False
        self._last_scene_pos = pos

        self.setPos(pos)

        # ── Identity ──────────────────────────────────────────────────────────
        self.node_id = node_id
        self.title = title
        self.uuid = uuid or _uuid.uuid4().hex
        self.node_type = "node"             # Overridden by subclasses for serialization routing

        # ── Resize state ──────────────────────────────────────────────────────
        # Corner drag resize — active when the bottom-right handle area is pressed.
        self._resize_handle_size = 12
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_rect = QRectF()

        # ── Ports ─────────────────────────────────────────────────────────────
        # ItemSendsScenePositionChanges must be set before _create_ports so
        # connections can track node movement via itemChange.
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.input_port = None
        self.output_port = None
        self._port_anim = None              # Reserved for future port show/hide animation
        self._create_ports()

        # ── Behaviour ─────────────────────────────────────────────────────────
        # NodeBehaviour owns the hover pulse animation entirely,
        # keeping animation logic off the Qt event loop.
        self.behaviour = NodeBehaviour(self)

        # ── Pen styling ───────────────────────────────────────────────────────
        # Pens are cached here to avoid recreating them on every paint call.
        self.normal_pen   = QPen(Theme.primaryBorder, Theme.nodeBorderWidth)
        self.hover_pen    = QPen(Theme.lighten(Theme.primaryBorder), Theme.nodeBorderWidth)
        self.current_pen  = self.normal_pen
        self._selected_pen = QPen(Theme.textPrimary, Theme.nodeBorderWidth * Theme.nodeBorderSelectedScale, Qt.SolidLine)

        # ── Qt item flags ─────────────────────────────────────────────────────
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges |
            QGraphicsRectItem.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        # ── Visuals ───────────────────────────────────────────────────────────
        self.setBrush(Theme.nodeDefaultBg)
        self.round_radius = Theme.nodeRoundRadius
        self.setPen(self.current_pen)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(Theme.nodeShadowBlur)
        shadow.setColor(Theme.nodeShadowColor)
        shadow.setOffset(Theme.nodeShadowOffsetX, Theme.nodeShadowOffsetY)
        self.setGraphicsEffect(shadow)

        # Scale animations (hover pulse) originate from the node center.
        self.setTransformOriginPoint(self.rect().center())

    # ─────────────────────────────────────────────────────────────────────────
    # POSITION TRACKING
    # ─────────────────────────────────────────────────────────────────────────

    def itemChange(self, change, value):
        """
        Intercept position changes to batch connection redraws via throttle timer.

        Sub-pixel movements (< 0.5px) are silently ignored to avoid flooding
        the update pipeline with noise from Qt's internal scene bookkeeping.
        A single-shot timer batches all movement during a drag into one
        connection update burst at the end of the throttle window.
        """
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            new_pos = self.scenePos()
            if self._last_scene_pos is not None:
                dx = abs(new_pos.x() - self._last_scene_pos.x())
                dy = abs(new_pos.y() - self._last_scene_pos.y())
                if dx < 0.5 and dy < 0.5:
                    return super().itemChange(change, value)
            self._last_scene_pos = new_pos
            self._pending_update = True
            if not self._update_throttle_timer:
                self._update_throttle_timer = QTimer()
                self._update_throttle_timer.setSingleShot(True)
                self._update_throttle_timer.timeout.connect(self._execute_pending_update)
                self._update_throttle_timer.start(Theme.nodeUpdateThrottle)
        return super().itemChange(change, value)

    def _execute_pending_update(self):
        """
        Flush the batched connection update after the throttle period.

        Guards against the node having been removed from the scene while
        the timer was still pending — a real scenario during rapid deletion.
        """
        self._update_throttle_timer = None
        if not self.scene():
            self._pending_update = False
            return
        if self._pending_update and hasattr(self, 'connections'):
            for conn in self.connections:
                conn.update_path()
            self.scene().set_dirty(True)
            self._pending_update = False

    # ─────────────────────────────────────────────────────────────────────────
    # PORTS
    # ─────────────────────────────────────────────────────────────────────────

    def _place_ports(self):
        """
        Position input and output ports at the vertical center of the node.

        Port vertical placement is derived from the node's current rect height,
        so this must be called after any geometry change. Horizontal nudge
        places ports slightly outside the node edges for comfortable clicking.
        Both values are controlled from Theme for global adjustment.
        """
        center_y = self.rect().height() / 2
        self.input_port.setPos(-Theme.portHorizontalNudge, center_y)
        self.output_port.setPos(self.rect().width() + Theme.portHorizontalNudge, center_y)

    def _create_ports(self):
        """
        Instantiate input and output ports as child items, hidden initially.

        Ports are created as children of this node so they inherit scene
        position changes automatically. They are hidden at birth and shown
        only when the user explicitly toggles them via right double-click.
        """
        self.input_port = Port(self, is_output=False)
        self.output_port = Port(self, is_output=True)
        self._place_ports()
        self.input_port.hide()
        self.output_port.hide()

    def setRect(self, rect):
        """
        Override to keep ports anchored and wires live-updated on resize.

        Called by Qt on any geometry change — including resize drags and
        session restore. Ports are repositioned immediately so they stay
        centered, and all connected wires are told to redraw so they follow
        the node edges in real time rather than waiting for the next move.
        """
        super().setRect(rect)
        if self.input_port and self.output_port:
            self._place_ports()
        for conn in self.connections:
            conn.update_path()

    def toggle_ports(self):
        """
        Flip port visibility and apply the new state.

        This is the only method that should change ports_visible — it owns
        the state flip. Call _sync_port_visibility() directly anywhere you
        need to apply the current state without toggling it.
        """
        self.ports_visible = not self.ports_visible
        self._sync_port_visibility()

    def _sync_port_visibility(self):
        """
        Apply the current ports_visible state to both ports without toggling.

        Call this after operations that affect port visibility indirectly —
        for example after connecting a wire, completing a resize, or restoring
        from session. Never flips ports_visible itself.
        """
        if self._port_anim and self._port_anim.state() == QAbstractAnimation.Running:
            self._port_anim.stop()
        if self.input_port:
            self.input_port.setVisible(self.ports_visible)
        if self.output_port:
            self.output_port.setVisible(self.ports_visible)

    # ─────────────────────────────────────────────────────────────────────────
    # MOUSE EVENTS
    # ─────────────────────────────────────────────────────────────────────────

    def on_port_clicked(self, port, event):
        """
        Entry point called directly by Port.mousePressEvent when a port is clicked.

        Starts a temporary floating wire from this node's output port.
        The wire follows the mouse until released on a target node,
        at which point the scene's mouseReleaseEvent finalises the connection.
        Only output ports initiate wires — input ports are passive receivers.
        """
        if port.is_output:
            from .Connection import Connection
            self.temp_connection = Connection(self)
            self.scene().addItem(self.temp_connection)

    def mousePressEvent(self, event):
        """
        Handle the three possible left-click interactions in priority order:

        1. Port handshake — fallback path if Port.mousePressEvent didn't fire directly.
           Checks whether the click landed on a child port and starts a wire if so.
        2. Resize handle — bottom-right corner drag initiates interactive resize.
        3. Standard drag — falls through to Qt's built-in item move behaviour.
        """
        if event.button() == Qt.LeftButton:
            # 1. PORT HANDSHAKE (fallback — primary path is Port.mousePressEvent)
            click_pos = event.scenePos()
            for child in self.childItems():
                if isinstance(child, Port):
                    if child.contains(child.mapFromScene(click_pos)):
                        if getattr(child, 'is_output', False):
                            from .Connection import Connection
                            self.temp_connection = Connection(self)
                            self.scene().addItem(self.temp_connection)
                            event.accept()
                            return

            # 2. RESIZE HANDLE — bottom-right 20x20 grab zone
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
        """
        Handle two live-drag modes: floating wire follow and corner resize stretch.

        Wire follow: updates the temp_connection path to the current mouse position
        so the wire appears to trail the cursor across the canvas.

        Resize stretch: recalculates node dimensions from the drag delta, clamped
        to minimum size. Shift-drag constrains to the original aspect ratio.
        """
        if self.temp_connection:
            self.temp_connection.update_path(event.scenePos())
            event.accept()
            return

        if self._is_resizing:
            delta = event.pos() - self._resize_start_pos
            new_width  = max(120, self._resize_start_rect.width()  + delta.x())
            new_height = max(50,  self._resize_start_rect.height() + delta.y())

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
        """
        Finalise an in-progress wire connection or a resize operation.

        For wire connections: checks whether the release landed on another node.
        If yes, the connection is registered on both endpoints and the wire is
        finalised. If no valid target, the wire is discarded and removed from the scene.

        For resize: clears the resize flag and syncs port visibility to match
        any show/hide state that may have changed during the drag.
        """
        if self._is_resizing:
            self._is_resizing = False
            self._sync_port_visibility()
            event.accept()

        if self.temp_connection:
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
        """
        Right double-click toggles port visibility on this node.

        Left double-click is intentionally unhandled at the BaseNode level —
        subclasses that want double-click behaviour (such as WarmNode opening
        its note editor) override this method and handle the left button there.
        """
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_ports()
            if self.scene():
                self.scene().set_dirty(True)
            event.accept()

    # ─────────────────────────────────────────────────────────────────────────
    # HOVER
    # ─────────────────────────────────────────────────────────────────────────

    def hoverEnterEvent(self, event):
        """
        Switch to hover pen and delegate pulse animation to NodeBehaviour.

        The pen swap gives immediate visual feedback. The pulse animation
        is handled entirely off the event loop by NodeBehaviour so the
        hover handler itself stays as lightweight as possible.
        """
        self.current_pen = self.hover_pen
        self.setPen(self.current_pen)
        self.update()
        self.behaviour.on_hover_enter()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Restore normal pen on hover leave.

        NodeBehaviour handles the reverse pulse animation autonomously —
        no explicit call needed here since the finished signal wired at
        NodeBehaviour init handles the settle-back.
        """
        self.current_pen = self.normal_pen
        self.setPen(self.current_pen)
        self.update()
        self.behaviour.on_hover_leave()
        super().hoverLeaveEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # PAINT PIPELINE
    # ─────────────────────────────────────────────────────────────────────────

    def paint(self, painter, option, widget):
        """
        Unified paint pipeline — Shell → LOD gate → Debug overlay → Grip → Specialist handoff.

        Step 1 — BODY: Draws the rounded rect shell with the appropriate border pen.
                  Uses cached pens to avoid per-frame QPen allocation.

        Step 2 — LOD GATE: Below Theme.nodeLodThreshold zoom level, suppresses the
                  drop shadow and returns early. This keeps zoomed-out scenes fast
                  by skipping work that's invisible at distance.

        Step 3 — DEBUG OVERLAY: When Theme.debugNodeOverlay is enabled (Settings →
                  General → Node Debug Overlay), draws bounding rect, shape path,
                  and port crosshairs in diagnostic colors for layout debugging.

        Step 4 — CORNER GRIP: Draws the resize grip asset at the bottom-right corner.
                  Isolated in _draw_corner_taper() so the asset can be swapped anytime.

        Step 5 — SPECIALIST HANDOFF: Calls paint_content() which subclasses override
                  to draw their type-specific content inside the node body.
        """
        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        rect = self.rect()

        # 1. BODY
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self._selected_pen if self.isSelected() else self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, self.round_radius, self.round_radius)

        # 2. LOD GATE
        if lod < Theme.nodeLodThreshold:
            if self.graphicsEffect():
                self.graphicsEffect().setEnabled(False)
            return
        if self.graphicsEffect():
            self.graphicsEffect().setEnabled(True)

        # 3. DEBUG OVERLAY
        if Theme.debugNodeOverlay:
            painter.save()
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2, Qt.DashLine))
            painter.setBrush(QColor(255, 255, 255, 40))
            painter.drawRect(self.boundingRect())
            painter.setPen(QPen(QColor(0, 255, 0, 200), 2, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self.shape())
            for port in [self.input_port, self.output_port]:
                if port:
                    p = port.pos()
                    painter.setPen(QPen(QColor(255, 255, 0, 255), 2))
                    painter.drawLine(int(p.x())-8, int(p.y()), int(p.x())+8, int(p.y()))
                    painter.drawLine(int(p.x()), int(p.y())-8, int(p.x()), int(p.y())+8)
            painter.restore()

        # 4. CORNER GRIP
        self._draw_corner_taper(painter)

        # 5. SPECIALIST HANDOFF
        self.paint_content(painter)

    def _draw_corner_taper(self, painter):
        """
        Draw the resize grip asset at the bottom-right corner.

        Isolated from the main paint pipeline so the grip image can be swapped
        for any custom asset by changing Theme.resizeGripImage — no paint code
        needs to change. The pixmap is lazy-loaded and cached by Theme.
        """
        pixmap = Theme.getResizeGripPixmap()
        if pixmap and not pixmap.isNull():
            br = self.rect().bottomRight()
            painter.drawPixmap(
                int(br.x()) - pixmap.width(),
                int(br.y()) - pixmap.height(),
                pixmap
            )

    def paint_content(self, painter):
        """
        Specialist paint handoff — override in subclasses to draw type-specific content.

        Called at the end of the BaseNode paint pipeline, after the shell,
        shadow, LOD gate, and resize grip have all been handled. The painter
        is in node-local coordinates. Base implementation is intentionally empty.
        """
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # GEOMETRY
    # ─────────────────────────────────────────────────────────────────────────

    def boundingRect(self):
        """
        Extend the bounding rect to include the drop shadow margin.

        Qt uses boundingRect() for repaint region calculations and culling.
        Without this extension, the shadow would be clipped during partial
        repaints and the shadow margin area would miss hover/click events.
        """
        return self.rect().adjusted(
            -Theme.nodeShadowMargin, -Theme.nodeShadowMargin,
             Theme.nodeShadowMargin,  Theme.nodeShadowMargin
        )

    def shape(self):
        """
        Match the hit-test shape to the full bounding rect including shadow margin.

        This ensures port click events reach mousePressEvent even when the
        cursor is slightly outside the visible node body but within the shadow
        area — important for the port handshake fallback path in mousePressEvent.
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    # ─────────────────────────────────────────────────────────────────────────
    # SERIALIZATION
    # ─────────────────────────────────────────────────────────────────────────

    def to_dict(self):
        """
        Serialize core node state to a dictionary for session persistence.

        Captures identity, position, geometry, and port visibility. Subclasses
        should call super().to_dict() and extend the returned dictionary with
        any additional state they need to restore — for example WarmNode adds
        full_text, BezierNode adds control point coordinates.
        """
        return {
            "node_id":       self.node_id,
            "uuid":          self.uuid,
            "type":          self.node_type,
            "title":         self.title,
            "pos_x":         self.pos().x(),
            "pos_y":         self.pos().y(),
            "width":         self.rect().width(),
            "height":        self.rect().height(),
            "ports_visible": self.ports_visible,
        }

    @staticmethod
    def from_dict(data: dict) -> 'BaseNode':
        """
        Factory method — routes session data to the correct subclass constructor.

        Reads the 'type' key from data and delegates to the appropriate
        subclass from_dict(). Uses local imports to avoid circular dependency
        issues at module load time. Falls back to a generic BaseNode if the
        type is unrecognised.

        Args:
            data: Dictionary containing serialized node state. Must include a
                  'type' key matching one of the registered node types.

        Returns:
            Fully constructed BaseNode subclass instance ready to add to the scene.
        """
        from .WarmNode import WarmNode
        from .ImageNode import ImageNode
        from .AboutNode import AboutNode
        from .BezierNode import BezierNode

        node_type = data.get("type", "node")

        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        elif node_type == "bezier":
            return BezierNode.from_dict(data)
        else:
            return BaseNode._create_from_dict(data)

    @staticmethod
    def _create_from_dict(data: dict) -> 'BaseNode':
        """
        Fallback factory for deserializing a generic BaseNode.

        Called by from_dict() when the node type is unrecognised — typically
        a node created before a subclass existed, or a future type not yet
        known to this version. Restores position, geometry, and port state.
        """
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