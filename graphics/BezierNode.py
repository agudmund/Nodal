#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - BezierNode.py bezier curve editor node
-A node that holds a live editable bezier curve for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QApplication
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, QEasingCurve
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QColor, QBrush,
    QPixmap, QLinearGradient, QFont
)
from .BaseNode import BaseNode
from .Theme import Theme
from utils.logger import setup_logger

logger = setup_logger()

# ─────────────────────────────────────────────────────────────────────────────
# CANVAS CONSTANTS
# Defines the inner drawing area inside the node where the curve lives.
# All handle positions are stored normalised (0.0–1.0) relative to this canvas,
# so the curve survives node resizing cleanly.
# ─────────────────────────────────────────────────────────────────────────────

CANVAS_MARGIN_X = 28        # Left/right inset from node edge
CANVAS_MARGIN_TOP = 48      # Top inset — leaves room for title area
CANVAS_MARGIN_BOTTOM = 28   # Bottom inset

HANDLE_RADIUS = 6           # Visual radius of the draggable handle circles
HIT_RADIUS = 12             # Larger hit radius for comfortable clicking

GRID_LINES = 4              # Number of subdivisions on each axis
REDRAW_THROTTLE_MS = 16     # ~60fps cap during active dragging


# ─────────────────────────────────────────────────────────────────────────────
# BEZIER HANDLE
# A draggable child item constrained to the canvas area of the parent node.
# Stores its logical position normalised so it survives node resize.
# Reports back to parent via _on_handle_moved() whenever it moves.
# ─────────────────────────────────────────────────────────────────────────────

class BezierHandle(QGraphicsEllipseItem):
    """
    Draggable control point handle living inside a BezierNode canvas.
    Position is normalised (0.0–1.0) relative to the canvas rect,
    so the curve shape is preserved when the node is resized.
    """

    def __init__(self, parent_node, norm_x: float, norm_y: float, color: QColor):
        """
        Args:
            parent_node: The BezierNode this handle belongs to
            norm_x: Initial normalised X position (0.0 = left, 1.0 = right)
            norm_y: Initial normalised Y position (0.0 = top, 1.0 = bottom)
            color:  Handle color — distinguishes the two control points visually
        """
        super().__init__(
            -HANDLE_RADIUS, -HANDLE_RADIUS,
            HANDLE_RADIUS * 2, HANDLE_RADIUS * 2,
            parent_node
        )
        self._node = parent_node
        self.norm_x = norm_x
        self.norm_y = norm_y

        self.setBrush(QBrush(color))
        self.setPen(QPen(color.lighter(160), 1.5))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.SizeAllCursor)
        self.setZValue(10)
        self._dragging = False
        self._drag_start_pos = QPointF()
        self._drag_start_item_pos = QPointF()

        self._sync_pos_from_norm()

    # ── Position sync ────────────────────────────────────────────────────────

    def canvas_rect(self) -> QRectF:
        """Returns the canvas rect in node-local coordinates."""
        return self._node._canvas_rect()

    def _sync_pos_from_norm(self):
        """Move the handle item to match its current normalised position."""
        cr = self.canvas_rect()
        x = cr.left() + self.norm_x * cr.width()
        y = cr.top() + self.norm_y * cr.height()
        self.setPos(x, y)

    def _sync_norm_from_pos(self):
        """Update normalised position from current item position, clamped to canvas."""
        cr = self.canvas_rect()
        if cr.width() <= 0 or cr.height() <= 0:
            return
        self.norm_x = max(0.0, min(1.0, (self.pos().x() - cr.left()) / cr.width()))
        self.norm_y = max(0.0, min(1.0, (self.pos().y() - cr.top()) / cr.height()))

    # ── Qt overrides ─────────────────────────────────────────────────────────

    def shape(self):
        """Return a larger hit area than the visual for comfortable clicking."""
        path = QPainterPath()
        path.addEllipse(-HIT_RADIUS, -HIT_RADIUS, HIT_RADIUS * 2, HIT_RADIUS * 2)
        return path

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self._node, '_handle1'):
                self._sync_norm_from_pos()
                self._node._on_handle_moved()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        """Deselect others on hover so drag starts from a clean state."""
        if self.scene():
            self.scene().clearSelection()
        self.setPen(QPen(Qt.white, 2))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Restore pen on leave."""
        self.setPen(QPen(self.brush().color().lighter(160), 1.5))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.scene():
                self.scene().clearSelection()
            self._dragging = True
            self._drag_start_pos = event.scenePos()
            self._drag_start_item_pos = self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.scenePos() - self._drag_start_pos
            # Convert scene delta to parent (node-local) coordinates
            new_pos = self._drag_start_item_pos + self.mapToParent(delta) - self.mapToParent(QPointF(0, 0))
            cr = self.canvas_rect()
            clamped = QPointF(
                max(cr.left(), min(cr.right(), new_pos.x())),
                max(cr.top(), min(cr.bottom(), new_pos.y()))
            )
            self.setPos(clamped)
            self._sync_norm_from_pos()
            self._node._on_handle_moved()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._sync_norm_from_pos()
            self._node._curve_dirty = True
            self._node.update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

# ─────────────────────────────────────────────────────────────────────────────
# BEZIER NODE
# ─────────────────────────────────────────────────────────────────────────────

class BezierNode(BaseNode):
    """
    A node containing a live editable cubic bezier curve.

    The curve runs from a fixed anchor at the left edge to a fixed anchor
    at the right edge of the canvas. Two draggable handles (CP1 and CP2)
    define the shape. This mirrors standard animation curve editors.

    Performance model:
        At rest — paint_content() blits a cached QPixmap. Nearly free.
        During drag — redraws into the cache at ~60fps via throttle timer.
        The node only redraws itself; the rest of the scene is unaffected.

    Output:
        get_easing_curve() returns a QEasingCurve ready for NodeBehaviour
        or any future data pipeline consumer.

    Serialisation:
        Extends BaseNode.to_dict() with the four normalised handle coordinates.
        from_dict() restores the curve exactly as it was left.
    """

    # Default handle positions — a gentle ease-in-out on first placement
    DEFAULT_CP1 = (0.25, 0.75)   # norm_x, norm_y  (lower-left area)
    DEFAULT_CP2 = (0.75, 0.25)   # norm_x, norm_y  (upper-right area)

    def __init__(self, node_id=0, title="Curve", pos=QPointF(0, 0),
                 width=280.0, height=220.0, uuid=None,
                 cp1=(None, None), cp2=(None, None)):
        """
        Args:
            node_id:  Scene node id
            title:    Label shown in the node header
            pos:      Scene position
            width:    Initial width  (minimum 200)
            height:   Initial height (minimum 180)
            uuid:     Serialisation id (auto-generated if None)
            cp1:      (norm_x, norm_y) for control point 1. Uses default if (None, None).
            cp2:      (norm_x, norm_y) for control point 2. Uses default if (None, None).
        """
        width  = max(200.0, width)
        height = max(180.0, height)

        super().__init__(node_id, title, pos, width, height, uuid)
        self.node_type = "bezier"
        self.setBrush(Theme.nodeDefaultBg)

        # ── Cache ─────────────────────────────────────────────────────────────
        self._curve_cache: QPixmap | None = None
        self._curve_dirty: bool = True          # True = must redraw cache

        # Throttle timer — caps redraw rate during handle dragging to ~60fps
        self._redraw_timer = QTimer()
        self._redraw_timer.setSingleShot(True)
        self._redraw_timer.timeout.connect(self._flush_cache)

        # ── Control point handles ─────────────────────────────────────────────
        cp1_x, cp1_y = cp1 if cp1[0] is not None else self.DEFAULT_CP1
        cp2_x, cp2_y = cp2 if cp2[0] is not None else self.DEFAULT_CP2

        self._handle1 = BezierHandle(self, cp1_x, cp1_y, QColor(Theme.wireStart))
        self._handle2 = BezierHandle(self, cp2_x, cp2_y, QColor(Theme.wireEnd))

        logger.debug(f"BezierNode [{self.uuid[:8]}] created at {pos}")

    # ─────────────────────────────────────────────────────────────────────────
    # CANVAS GEOMETRY
    # ─────────────────────────────────────────────────────────────────────────

    def _canvas_rect(self) -> QRectF:
        """The inner drawing area in node-local coordinates."""
        r = self.rect()
        return QRectF(
            r.left()   + CANVAS_MARGIN_X,
            r.top()    + CANVAS_MARGIN_TOP,
            r.width()  - CANVAS_MARGIN_X * 2,
            r.height() - CANVAS_MARGIN_TOP - CANVAS_MARGIN_BOTTOM
        )

    def _anchor_left(self) -> QPointF:
        """Fixed start anchor — bottom-left of canvas (value = 0 at time = 0)."""
        cr = self._canvas_rect()
        return QPointF(cr.left(), cr.bottom())

    def _anchor_right(self) -> QPointF:
        """Fixed end anchor — top-right of canvas (value = 1 at time = 1)."""
        cr = self._canvas_rect()
        return QPointF(cr.right(), cr.top())

    def _handle1_scene_pos(self) -> QPointF:
        """Handle 1 position in node-local coordinates."""
        return self._handle1.pos()

    def _handle2_scene_pos(self) -> QPointF:
        """Handle 2 position in node-local coordinates."""
        return self._handle2.pos()

    # ─────────────────────────────────────────────────────────────────────────
    # HANDLE CALLBACK
    # ─────────────────────────────────────────────────────────────────────────

    def _on_handle_moved(self):
        """
        Called by BezierHandle.itemChange on every position change.
        Sets the dirty flag and schedules a throttled cache flush rather than
        redrawing immediately — prevents excessive redraws during fast drags.
        """
        self._curve_dirty = True
        if not self._redraw_timer.isActive():
            self._redraw_timer.start(REDRAW_THROTTLE_MS)
        self.propagate_output()

    # ─────────────────────────────────────────────────────────────────────────
    # CACHE MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def _flush_cache(self):
        """Redraw the curve into the pixmap cache and trigger a visual update."""
        self._curve_dirty = True   # ensure paint_content triggers a redraw
        self.update()

    def _rebuild_cache(self, painter_scale: float = 1.0):
        """
        Render the full curve canvas into self._curve_cache.
        Called only when _curve_dirty is True.
        Returns the freshly built pixmap.
        """
        cr = self._canvas_rect()
        if cr.width() <= 0 or cr.height() <= 0:
            return None

        w = int(cr.width())
        h = int(cr.height())

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)

        # Offset so we paint relative to top-left of canvas
        p.translate(-cr.left(), -cr.top())

        self._paint_grid(p, cr)
        self._paint_tangent_lines(p, cr)
        self._paint_curve(p, cr)
        self._paint_anchors(p, cr)
        self._paint_label(p, cr)

        p.end()

        self._curve_cache = pixmap
        self._curve_dirty = False
        return pixmap

    # ─────────────────────────────────────────────────────────────────────────
    # PAINT PIPELINE — specialist handoff from BaseNode.paint()
    # ─────────────────────────────────────────────────────────────────────────

    def paint_content(self, painter: QPainter):
        """
        Blit the cached curve canvas. Rebuild cache only when dirty.
        At rest this is a single drawPixmap call — essentially free.
        """
        cr = self._canvas_rect()
        if cr.width() <= 0 or cr.height() <= 0:
            return

        if self._curve_dirty or self._curve_cache is None:
            self._rebuild_cache()

        if self._curve_cache:
            painter.drawPixmap(int(cr.left()), int(cr.top()), self._curve_cache)

    # ─────────────────────────────────────────────────────────────────────────
    # CANVAS DRAWING PRIMITIVES
    # All paint in node-local coordinates (canvas origin already translated)
    # ─────────────────────────────────────────────────────────────────────────

    def _paint_grid(self, painter: QPainter, cr: QRectF):
        """Subtle grid subdivisions — gives spatial reference for curve reading."""
        grid_pen = QPen(QColor(255, 255, 255, 18), 1, Qt.DotLine)
        painter.setPen(grid_pen)

        for i in range(1, GRID_LINES):
            t = i / GRID_LINES
            # Vertical
            x = cr.left() + t * cr.width()
            painter.drawLine(int(x), int(cr.top()), int(x), int(cr.bottom()))
            # Horizontal
            y = cr.top() + t * cr.height()
            painter.drawLine(int(cr.left()), int(y), int(cr.right()), int(y))

        # Canvas border
        border_pen = QPen(QColor(255, 255, 255, 30), 1)
        painter.setPen(border_pen)
        painter.drawRect(cr)

    def _paint_tangent_lines(self, painter: QPainter, cr: QRectF):
        """
        Thin lines from anchors to their respective control point handles.
        Classic animation curve editor visual — helps read the tangent direction.
        """
        tangent_pen = QPen(QColor(255, 255, 255, 45), 1, Qt.DashLine)
        painter.setPen(tangent_pen)

        p0 = self._anchor_left()
        p3 = self._anchor_right()
        p1 = self._handle1_scene_pos()
        p2 = self._handle2_scene_pos()

        painter.drawLine(p0, p1)
        painter.drawLine(p3, p2)

    def _paint_curve(self, painter: QPainter, cr: QRectF):
        """
        The actual bezier curve — drawn with the same glow + core layering
        as Connection.py for visual consistency with the wires in the graph.
        """
        p0 = self._anchor_left()
        p1 = self._handle1_scene_pos()
        p2 = self._handle2_scene_pos()
        p3 = self._anchor_right()

        path = QPainterPath()
        path.moveTo(p0)
        path.cubicTo(p1, p2, p3)

        # Glow layer
        grad = QLinearGradient(p0, p3)
        grad.setColorAt(0, Theme.wireStart)
        grad.setColorAt(1, Theme.wireEnd)
        glow_pen = QPen(QBrush(grad), 5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(path)

        # Core layer
        core_pen = QPen(QColor(255, 255, 255, 180), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(core_pen)
        painter.drawPath(path)

    def _paint_anchors(self, painter: QPainter, cr: QRectF):
        """Fixed anchor diamonds at curve start and end."""
        painter.setPen(QPen(QColor(255, 255, 255, 140), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 60)))

        for anchor in [self._anchor_left(), self._anchor_right()]:
            diamond = QPainterPath()
            s = 5  # half-size of diamond
            diamond.moveTo(anchor.x(),     anchor.y() - s)
            diamond.lineTo(anchor.x() + s, anchor.y())
            diamond.lineTo(anchor.x(),     anchor.y() + s)
            diamond.lineTo(anchor.x() - s, anchor.y())
            diamond.closeSubpath()
            painter.drawPath(diamond)

    def _paint_label(self, painter: QPainter, cr: QRectF):
        """
        Small normalised coordinate readout for each handle.
        Gives numeric feedback without needing a separate panel.
        """
        painter.setPen(QColor(255, 255, 255, 80))
        font = QFont(Theme.nodeBodyFontFamily, 7)
        painter.setFont(font)

        for handle in [self._handle1, self._handle2]:
            pos = handle.pos()
            label = f"{handle.norm_x:.2f}, {1.0 - handle.norm_y:.2f}"
            # Offset label slightly above handle
            painter.drawText(int(pos.x()) + 8, int(pos.y()) - 4, label)

    # ─────────────────────────────────────────────────────────────────────────
    # OUTPUT — the reason this node exists
    # ─────────────────────────────────────────────────────────────────────────

    def get_easing_curve(self) -> QEasingCurve:
        """
        Returns a QEasingCurve.BezierSpline built from the current handle positions.
        Ready to hand directly to NodeBehaviour or any future data pipeline consumer.

        The curve maps normalised time (X) to normalised value (Y), consistent with
        how Qt and most animation systems interpret bezier easing curves.

        Note: Qt BezierSpline expects Y to increase upward, but canvas Y increases
        downward — so we invert norm_y here.
        """
        curve = QEasingCurve(QEasingCurve.BezierSpline)
        curve.addCubicBezierSegment(
            QPointF(self._handle1.norm_x, 1.0 - self._handle1.norm_y),
            QPointF(self._handle2.norm_x, 1.0 - self._handle2.norm_y),
            QPointF(1.0, 1.0)
        )
        return curve

    def copy_curve_to_clipboard(self):
        """
        Copies the control point values as a Python-ready string to the clipboard.
        Paste directly into NodeBehaviour or anywhere a QEasingCurve is consumed.

        Example output:
            # BezierNode curve — paste into NodeBehaviour or similar
            curve = QEasingCurve(QEasingCurve.BezierSpline)
            curve.addCubicBezierSegment(
                QPointF(0.25, 0.80),
                QPointF(0.75, 0.20),
                QPointF(1.0, 1.0)
            )
        """
        cp1 = QPointF(self._handle1.norm_x, 1.0 - self._handle1.norm_y)
        cp2 = QPointF(self._handle2.norm_x, 1.0 - self._handle2.norm_y)

        text = (
            f"# BezierNode curve — paste into NodeBehaviour or similar\n"
            f"curve = QEasingCurve(QEasingCurve.BezierSpline)\n"
            f"curve.addCubicBezierSegment(\n"
            f"    QPointF({cp1.x():.4f}, {cp1.y():.4f}),\n"
            f"    QPointF({cp2.x():.4f}, {cp2.y():.4f}),\n"
            f"    QPointF(1.0, 1.0)\n"
            f")"
        )
        QApplication.clipboard().setText(text)
        logger.info(f"BezierNode [{self.uuid[:8]}] curve copied to clipboard")

    def propagate_output(self):
        """Push current curve values to any connected WarmNodes."""
        if not hasattr(self, '_handle2') or self._handle2 is None:
            return  # Called during init before both handles exist
        from .WarmNode import WarmNode
        cp1 = QPointF(self._handle1.norm_x, 1.0 - self._handle1.norm_y)
        cp2 = QPointF(self._handle2.norm_x, 1.0 - self._handle2.norm_y)
        text = (
            f"Bezier Curve Output\n\n"
            f"CP1: ({cp1.x():.4f}, {cp1.y():.4f})\n"
            f"CP2: ({cp2.x():.4f}, {cp2.y():.4f})\n\n"
            f"# Ready to paste:\n"
            f"curve.addCubicBezierSegment(\n"
            f"    QPointF({cp1.x():.4f}, {cp1.y():.4f}),\n"
            f"    QPointF({cp2.x():.4f}, {cp2.y():.4f}),\n"
            f"    QPointF(1.0, 1.0)\n"
            f")"
        )
        for conn in self.connections:
            if conn.end_node and isinstance(conn.end_node, WarmNode):
                conn.end_node.receive_data(text)

    # ─────────────────────────────────────────────────────────────────────────
    # DOUBLE CLICK — copy curve to clipboard
    # ─────────────────────────────────────────────────────────────────────────

    def mouseDoubleClickEvent(self, event):
        """Left double-click copies the current curve to clipboard."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.copy_curve_to_clipboard()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # SERIALISATION
    # ─────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Extend base serialisation with the four normalised handle coordinates."""
        data = super().to_dict()
        data["cp1_x"] = self._handle1.norm_x
        data["cp1_y"] = self._handle1.norm_y
        data["cp2_x"] = self._handle2.norm_x
        data["cp2_y"] = self._handle2.norm_y
        return data

    @staticmethod
    def from_dict(data: dict) -> 'BezierNode':
        """Deserialise a BezierNode from session data, restoring curve exactly."""
        node = BezierNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Curve"),
            pos=QPointF(data.get("pos_x", 0.0), data.get("pos_y", 0.0)),
            width=float(data.get("width", 280.0)),
            height=float(data.get("height", 220.0)),
            uuid=data.get("uuid"),
            cp1=(data.get("cp1_x"), data.get("cp1_y")),
            cp2=(data.get("cp2_x"), data.get("cp2_y")),
        )
        node.ports_visible = data.get("ports_visible", False)
        return node