#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - scene.py graphics scene management
-Handles node scene, blur effects, and background rendering for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import ctypes
import sys
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsBlurEffect, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QPainter, QTransform
from .Theme import Theme
from utils.motivational_messages import motivationalMessages
from .BaseNode import BaseNode
from .WarmNode import WarmNode
from .BezierNode import BezierNode
from utils.logger import setup_logger, TRACE

logger = setup_logger()


# ─────────────────────────────────────────────────────────────────────────────
# WINDOWS MICA BLUR
# ─────────────────────────────────────────────────────────────────────────────

def enable_blur(hwnd):
    """Enable Windows Mica blur effect on the window (Windows only).
    Silently skips on non-Windows platforms — broad catch is intentional.
    """
    if sys.platform != "win32":
        return  # Non-Windows platforms won't have ctypes.windll — broad catch is intentional

    if not hwnd:
        return

    try:
        class WindowCompositionAttributeData(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p), ("SizeOfData", ctypes.c_size_t)]
        class AccentPolicy(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]

        accent = AccentPolicy()
        # AccentState 5 = Mica effect
        # AccentFlags 0 = let Windows handle tinting, not us
        accent.AccentState = 5
        accent.AccentFlags = 0
        accent.GradientColor = 0x00000000  # Fully transparent base

        data = WindowCompositionAttributeData()
        data.Attribute = 19
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)

        # Convert QColor to Windows ABGR format (0xAA BB GG RR)
        tint = Theme.frostColor
        windows_color = (tint.alpha() << 24) | (tint.blue() << 16) | (tint.green() << 8) | tint.red()
        accent.GradientColor = windows_color

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Warning: Could not enable blur effect: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# NODE SCENE
# ─────────────────────────────────────────────────────────────────────────────

class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dirty = False
        self._undo_stack = []   # Each entry: list of (node_dict, [conn_dicts]) for one delete action
        self._undo_max = 30     # Cap memory use — oldest actions fall off the back

        # Recovery: debounced write so rapid dirty events collapse into one disk hit
        from utils.settings import Settings
        self._recovery_timer = QTimer()
        self._recovery_timer.setSingleShot(True)
        self._recovery_timer.setInterval(Settings.get_recovery_interval() * 1000)
        self._recovery_timer.timeout.connect(self._write_recovery)

        # Only try to enable blur if we actually have a parent window
        if parent and hasattr(parent, 'winId'):
            enable_blur(parent.winId())

        self.temp_conn = None
        self.setSceneRect(-1000, -1000, 1000, 1000)  # Give yourself room to roam

        # THE FOG LAYER — a transparent rect that holds the background blur effect.
        # The effect is applied to the layer, not the view, for performance reasons.
        self.fog_layer = QGraphicsRectItem(self.sceneRect())
        self.fog_layer.setRect(-1000, -1000, 1000, 1000)
        self.fog_layer.setBrush(Qt.NoBrush)
        self.fog_layer.setPen(Qt.NoPen)
        self.fog_layer.setZValue(-100)  # Deep in the background

        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)  # Faster during slider-dragging
        self.fog_layer.setGraphicsEffect(self.blur_effect)
        self.addItem(self.fog_layer)

    # ─────────────────────────────────────────────────────────────────────────
    # DIRTY STATE
    # ─────────────────────────────────────────────────────────────────────────

    def set_dirty(self, value: bool):
        """Update dirty state and schedule a recovery snapshot on any change."""
        if self._dirty != value:
            self._dirty = value
            # Here is where you'd eventually tell the Save Button to glow!
        if value:
            self._recovery_timer.start()  # Restart the quiet timer on every dirty event

    def is_dirty(self) -> bool:
        return self._dirty

    # ─────────────────────────────────────────────────────────────────────────
    # WIRE TRACKING — scene-level mouse handling for floating connection wires
    # ─────────────────────────────────────────────────────────────────────────

    def _get_active_wire_node(self):
        """Return the node currently dragging a temp_connection, or None."""
        for item in self.items():
            if isinstance(item, BaseNode) and getattr(item, 'temp_connection', None):
                return item
        return None

    def mouseMoveEvent(self, event):
        """Track floating wire at scene level so it follows the mouse anywhere."""
        node = self._get_active_wire_node()
        if node:
            node.temp_connection.update_path(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Complete or cancel floating wire at scene level."""
        node = self._get_active_wire_node()
        if node:
            items = self.items(event.scenePos())
            target_node = next((i for i in items if isinstance(i, BaseNode) and i is not node), None)
            if target_node:
                conn = node.temp_connection
                conn.end_node = target_node
                if conn not in node.connections:
                    node.connections.append(conn)
                if conn not in target_node.connections:
                    target_node.connections.append(conn)
                target_node._sync_port_visibility()
                conn.update_path()
                self.set_dirty(True)
            else:
                self.removeItem(node.temp_connection)
            node.temp_connection = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # SESSION PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def _write_recovery(self):
        """Write the full scene state to sessions/recovery.json as a silent safety net."""
        from utils.session_manager import SessionManager
        try:
            data = self.get_session_data()
            path = SessionManager.get_session_filename("recovery")
            SessionManager.save_session(path, data)
        except Exception as e:
            logger.warning(f"Recovery write failed: {e}")

    def get_session_data(self) -> dict:
        """Gather all nodes and connections for session persistence.

        Returns:
            Dictionary with version, serialized nodes, and connection metadata.
        """
        # 1. Gather Nodes
        nodes_data = [item.to_dict() for item in self.items() if isinstance(item, BaseNode)]

        # 2. Gather Connections — The Nerve Ledger
        from graphics.Connection import Connection
        conns_data = []
        for item in self.items():
            if isinstance(item, Connection):
                conns_data.append({
                    "start_node_uuid": item.start_node.uuid,
                    "end_node_uuid": item.end_node.uuid if item.end_node else None
                })

        return {
            "version": "1.0",
            "nodes": nodes_data,
            "connections": conns_data
        }

    def rebuild_from_session(self, data: dict):
        """Reconstruct scene nodes and connections from session data.
        Clears existing nodes and rebuilds graph from serialized state.

        Args:
            data: Dictionary with 'nodes' and 'connections' lists from session
        """
        from graphics.Connection import Connection

        # NOTE: load_session already calls clear_nodes() before invoking this method.
        # Do not call it again here — a double clear fires invalidate()+viewport.update()
        # mid-rebuild while nodes are being added, causing ghost renders.
        node_map = {}  # UUID → node, used for reconnecting wires in second pass

        # 1. First Pass: Create all Nodes
        for node_data in data.get("nodes", []):
            new_node = BaseNode.from_dict(node_data)
            new_node.setZValue(10)
            self.addItem(new_node)
            effect_name = type(new_node.graphicsEffect()).__name__ if new_node.graphicsEffect() else "None"
            logger.log(
                TRACE,
                f"[REBUILD] node id={new_node.node_id} type={new_node.node_type} "
                f"z={new_node.zValue()} pos=({new_node.pos().x():.1f},{new_node.pos().y():.1f}) "
                f"size=({new_node.rect().width():.0f}x{new_node.rect().height():.0f}) "
                f"effect={effect_name} _paint_debug_count={new_node._paint_debug_count}"
            )
            node_map[new_node.uuid] = new_node

        # 2. Second Pass: Re-plug the Nerves
        for conn_data in data.get("connections", []):
            start_node = node_map.get(conn_data.get("start_node_uuid"))
            end_node = node_map.get(conn_data.get("end_node_uuid"))
            if start_node and end_node:
                new_conn = Connection(start_node, end_node)
                self.addItem(new_conn)

    # ─────────────────────────────────────────────────────────────────────────
    # NODE CREATION HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _next_node_id(self) -> int:
        """Auto-increment node id based on current scene node count."""
        return len([item for item in self.items() if isinstance(item, BaseNode)])

    def _register_node(self, node: BaseNode) -> BaseNode:
        """Common finalisation for any newly created node — add to scene, set Z, mark dirty."""
        node.setZValue(10)
        self.addItem(node)
        self.set_dirty(True)
        return node

    def add_warm_node(self, x: float, y: float, title: str = None) -> 'WarmNode':
        """Create and add a WarmNode to the scene.
        Uses a random motivational message as title if not provided.

        Args:
            x: Scene X coordinate
            y: Scene Y coordinate
            title: Optional node title (uses random motivational message if None)

        Returns:
            Newly created WarmNode instance
        """
        if title is None:
            title = random.choice(motivationalMessages)
        node = WarmNode(
            node_id=self._next_node_id(),
            title=title,
            pos=QPointF(x, y)
        )
        return self._register_node(node)

    def add_bezier_node(self, x: float, y: float, title: str = "Curve") -> 'BezierNode':
        """Create and add a BezierNode to the scene.
        Arrives with a default gentle ease-in-out curve, ready to shape.

        Args:
            x: Scene X coordinate
            y: Scene Y coordinate
            title: Optional node title (default: 'Curve')

        Returns:
            Newly created BezierNode instance
        """
        node = BezierNode(
            node_id=self._next_node_id(),
            title=title,
            pos=QPointF(x, y)
        )
        return self._register_node(node)

    def add_node(self, x: float, y: float, title: str = None) -> 'WarmNode':
        """Backwards-compatible alias for add_warm_node.
        🪟 Prefer add_warm_node() or add_bezier_node() for new call sites.
        """
        return self.add_warm_node(x, y, title)

    # ─────────────────────────────────────────────────────────────────────────
    # CONNECTION CREATION
    # ─────────────────────────────────────────────────────────────────────────

    def add_connection(self, node_a: BaseNode, node_b: BaseNode):
        """Create and register a visual connection (wire) between two nodes.

        Args:
            node_a: Source BaseNode
            node_b: Target BaseNode

        Returns:
            Connection instance
        """
        from graphics.Connection import Connection
        conn = Connection(node_a, node_b)
        self.addItem(conn)
        node_a.connections.append(conn)
        node_b.connections.append(conn)
        return conn

    # ─────────────────────────────────────────────────────────────────────────
    # SCENE CLEANUP
    # ─────────────────────────────────────────────────────────────────────────

    def clear_nodes(self):
        """Remove all nodes from the scene while preserving the background fog layer.
        Properly cleans up graphics effects and invalidates the scene cache.
        """
        # 1. Grab only top-level items — child items (ports) are cleaned up automatically
        # when their parent node is removed. Iterating all items including children and
        # calling removeItem on them causes Qt to unparent children into orphaned scene
        # items rather than removing them, which is the root cause of ghost node rendering.
        all_items = self.items()
        top_level_items = [i for i in all_items if i.parentItem() is None]
        node_count = sum(1 for i in top_level_items if isinstance(i, BaseNode))
        logger.log(TRACE, f"[CLEAR_NODES] removing {len(top_level_items)} top-level items ({node_count} nodes) from scene")

        # 2. THE ULTIMATUM: If it's not the Fog, it's gone.
        # Only remove top-level items — their children (ports, etc.) follow automatically.
        # Do NOT call setGraphicsEffect(None) before removeItem — doing so schedules a
        # deferred repaint on the item which fires AFTER removal, producing ghost renders.
        # The effect is destroyed cleanly by Qt when the item is removed.
        for item in top_level_items:
            if item != self.fog_layer:
                self.removeItem(item)

        # 3. THE GHOST BUSTER: Invalidate the entire visual cache
        self.invalidate(self.sceneRect(), QGraphicsScene.AllLayers)

        # 4. Notify the cameras
        for view in self.views():
            view.viewport().update()

        # 5. Post-clear verification — log any survivors that should not be here
        survivors = [i for i in self.items() if i != self.fog_layer]
        if survivors:
            for s in survivors:
                logger.log(TRACE, f"[CLEAR_NODES] SURVIVOR: {type(s).__name__} parentItem={type(s.parentItem()).__name__ if s.parentItem() else None} scene={s.scene() is not None}")
        logger.log(TRACE, f"[CLEAR_NODES] scene cleared — {len(survivors)} survivors (expected 0)")

    # ─────────────────────────────────────────────────────────────────────────
    # KEYBOARD — delete and undo
    # ─────────────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        """Delete selected nodes with Backspace/Delete, undo last delete with Ctrl+Z."""
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            selected_nodes = [item for item in self.selectedItems() if isinstance(item, BaseNode)]
            if selected_nodes:
                from graphics.Connection import Connection
                snapshot = []
                for node in selected_nodes:
                    node_dict = node.to_dict()
                    conn_dicts = []
                    for conn in list(node.connections):
                        if conn.end_node:
                            conn_dicts.append({
                                "start_node_uuid": conn.start_node.uuid,
                                "end_node_uuid": conn.end_node.uuid,
                            })
                        if conn.scene():
                            self.removeItem(conn)
                        for endpoint in (conn.start_node, conn.end_node):
                            if endpoint and endpoint is not node and conn in endpoint.connections:
                                endpoint.connections.remove(conn)
                    node.connections.clear()
                    if node.scene():
                        self.removeItem(node)
                    snapshot.append((node_dict, conn_dicts))

                self._undo_stack.append(snapshot)
                if len(self._undo_stack) > self._undo_max:
                    self._undo_stack.pop(0)
                self.set_dirty(True)
                event.accept()
                return

        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if self._undo_stack:
                self._undo_delete(self._undo_stack.pop())
                event.accept()
                return

        super().keyPressEvent(event)

    def _undo_delete(self, snapshot):
        """Restore a deleted set of nodes and reconnect any wires whose both endpoints exist."""
        from graphics.Connection import Connection
        uuid_map = {item.uuid: item for item in self.items() if isinstance(item, BaseNode)}

        restored = {}
        for node_dict, _ in snapshot:
            node = BaseNode.from_dict(node_dict)
            node.setZValue(10)
            self.addItem(node)
            restored[node.uuid] = node

        uuid_map.update(restored)

        for _, conn_dicts in snapshot:
            for cd in conn_dicts:
                start = uuid_map.get(cd["start_node_uuid"])
                end = uuid_map.get(cd["end_node_uuid"])
                if start and end:
                    conn = Connection(start, end)
                    self.addItem(conn)

        self.set_dirty(True)

    # ─────────────────────────────────────────────────────────────────────────
    # BACKGROUND
    # ─────────────────────────────────────────────────────────────────────────

    def drawBackground(self, painter, rect):
        bg_color = Theme.with_alpha(Theme.frostColor, Theme.frostColor.alpha())
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)