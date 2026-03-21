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
from .BezierNode import BezierNode
from .HealthNode import HealthNode
from .ImageNode import ImageNode
from .WarmNode import WarmNode
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
        self.active_node_registry = {} # The global ledger for the current session

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

    _IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

    def dragEnterEvent(self, event):
        """Accept drag events that carry at least one recognised image file URL."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if any(url.toLocalFile().lower().endswith(e) for e in self._IMAGE_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        """Keep the drag accepted as the cursor moves across the scene."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if any(url.toLocalFile().lower().endswith(e) for e in self._IMAGE_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """
        Create an ImageNode for each dropped image file.
        Multiple files in one drop each get their own node, staggered slightly
        so they don't land exactly on top of each other.
        """
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        image_paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(e) for e in self._IMAGE_EXTENSIONS)
        ]

        if not image_paths:
            event.ignore()
            return

        base_pos = event.scenePos()
        STAGGER = 20

        for i, path in enumerate(image_paths):
            self.add_image_node(
                base_pos.x() + i * STAGGER,
                base_pos.y() + i * STAGGER,
                path=path
            )

        event.acceptProposedAction()
        
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
        """
        Reconstruct scene nodes and connections from session data.

        Two-pass rebuild:
        Pass 1 — create all nodes and register them by UUID in active_node_registry.
        Pass 2 — reconnect wires using the registry so UUIDs resolve correctly.

        Registry is cleared before rebuild so stale UUIDs from previous sessions
        cannot cause wires to connect to wrong nodes. Sessions are independent graphs.

        Uses addItem() directly rather than _register_node() — _register_node calls
        set_dirty(True) which is wrong during a load. The session is not dirty just
        because we restored it.
        """
        logger.log(TRACE, f"[REBUILD] ═══ REBUILD START ═══")
        logger.log(TRACE, f"[REBUILD] clearing active_node_registry (had {len(self.active_node_registry)} entries)")
        self.active_node_registry.clear()

        nodes_data = data.get("nodes", [])
        conns_data = data.get("connections", [])
        logger.log(TRACE, f"[REBUILD] session data: {len(nodes_data)} nodes, {len(conns_data)} connections")

        # ── PASS 1: Create nodes ──────────────────────────────────────────────
        logger.log(TRACE, f"[REBUILD] pass 1 — creating nodes")
        for i, node_data in enumerate(nodes_data):
            node_type = node_data.get("type", "unknown")
            node_title = node_data.get("title", "untitled")
            node_uuid = node_data.get("uuid", "no-uuid")[:8]
            logger.log(TRACE, f"[REBUILD] pass 1 [{i}] — type={node_type} title='{node_title}' uuid={node_uuid}")
            try:
                new_node = BaseNode.from_dict(node_data)
                new_node.setZValue(10)
                self.addItem(new_node)
                self.active_node_registry[new_node.uuid] = new_node
                logger.log(TRACE, f"[REBUILD] pass 1 [{i}] — added to scene and registry ✅")
            except Exception as e:
                logger.error(
                    f"[REBUILD] pass 1 [{i}] — FAILED to create node type={node_type} title='{node_title}': "
                    f"{type(e).__name__}: {e}",
                    exc_info=True
                )

        logger.log(TRACE, f"[REBUILD] pass 1 complete — {len(self.active_node_registry)} nodes in registry")

        # ── PASS 2: Reconnect wires ───────────────────────────────────────────
        logger.log(TRACE, f"[REBUILD] pass 2 — reconnecting wires")
        from graphics.Connection import Connection
        wires_connected = 0
        wires_skipped = 0
        for i, conn_data in enumerate(conns_data):
            start_uuid = conn_data.get("start_node_uuid")
            end_uuid   = conn_data.get("end_node_uuid")
            start = self.active_node_registry.get(start_uuid)
            end   = self.active_node_registry.get(end_uuid)
            logger.log(TRACE,
                f"[REBUILD] pass 2 [{i}] — "
                f"start={start_uuid[:8] if start_uuid else 'None'} found={start is not None} | "
                f"end={end_uuid[:8] if end_uuid else 'None'} found={end is not None}"
            )
            if start and end:
                try:
                    new_conn = Connection(start, end)
                    self.addItem(new_conn)
                    wires_connected += 1
                    logger.log(TRACE, f"[REBUILD] pass 2 [{i}] — wire connected ✅")
                except Exception as e:
                    logger.error(
                        f"[REBUILD] pass 2 [{i}] — FAILED to create connection: {type(e).__name__}: {e}",
                        exc_info=True
                    )
                    wires_skipped += 1
            else:
                wires_skipped += 1
                logger.warning(
                    f"[REBUILD] pass 2 [{i}] — skipped wire: "
                    f"start {'missing' if not start else 'ok'} | end {'missing' if not end else 'ok'}"
                )

        logger.log(TRACE,
            f"[REBUILD] pass 2 complete — {wires_connected} wires connected, {wires_skipped} skipped"
        )
        logger.log(TRACE, f"[REBUILD] ═══ REBUILD COMPLETE ═══")

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

    def add_health_node(self, x: float, y: float) -> 'HealthNode':
        node = HealthNode(node_id=self._next_node_id(), pos=QPointF(x, y))
        return self._register_node(node)

    def add_image_node(self, x: float, y: float, path: str = None) -> 'ImageNode':
        """
        Create and add an ImageNode to the scene.

        Args:
            x:    Scene X coordinate for the new node.
            y:    Scene Y coordinate for the new node.
            path: Optional file path to load immediately.
                  If None, the node arrives empty — double-click to browse.

        Returns:
            Newly created ImageNode instance.
        """
        node = ImageNode(
            node_id=self._next_node_id(),
            pos=QPointF(x, y)
        )
        self._register_node(node)
        if path:
            node.load_from_path(path)
        return node

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

    def purge_session_items(self):
        """
        Full session purge — removes all nodes, connections, and orphaned items.

        Designed to be as clean as a fresh app launch. The only reason a session
        switcher exists at all is to avoid restarting the app — everything else
        should behave identically to a relaunch.

        Step-by-step with TRACE logging at every gate so no failure is silent:

        0. Undo stack clear — session undo history must not survive into a new session.
        1. Mouse grab release — prevents ungrabMouse errors if a node was mid-drag.
        2. Floating wire cleanup — orphaned temp_connections severed and removed.
        3. Orphaned QGraphicsTextItem sweep — WarmNode child text items that survived
           a previous purge as top-level orphans. These look like complete nodes but
           have no BaseNode backing. Identified via the HealthNode click spy (type=QGraphicsTextItem,
           identity=memory_address, no title, no uuid).
        4. Gather all purgeable items — BaseNode, Connection, orphaned QGraphicsTextItem,
           all top-level (parentItem is None), none of them the fog layer.
        5. Pre-cleanup — stop animations and sever connection references while items
           are still in the scene so Qt APIs are valid.
        6. Batch removal — removeItem for each gathered item.
        7. GC sweep — force Python to collect what we just severed rather than
           waiting for its own schedule. Session switches are launch-equivalent.
        8. Scene invalidation — flush any deferred repaints from removed items.
        9. Dirty reset and visual refresh.
        """
        from .BaseNode import BaseNode
        from .Connection import Connection
        from PySide6.QtWidgets import QGraphicsTextItem
        import gc as _gc

        logger.log(TRACE, f"[PURGE] ═══ SESSION PURGE START ═══")
        logger.log(TRACE, f"[PURGE] scene item count before purge: {len(self.items())}")

        # ── STEP 0: Clear undo stack ──────────────────────────────────────────
        # Session undo history must never bleed into a different session.
        logger.log(TRACE, f"[PURGE] step 0 — clearing undo stack ({len(self._undo_stack)} entries)")
        self._undo_stack.clear()
        logger.log(TRACE, f"[PURGE] step 0 — undo stack cleared")

        # ── STEP 1: Release mouse grab ────────────────────────────────────────
        # If a node is mid-drag when the scene is cleared, Qt throws:
        # "QGraphicsItem::ungrabMouse: cannot ungrab mouse without scene"
        grabber = self.mouseGrabberItem()
        active_wires = [i for i in self.items() if isinstance(i, BaseNode) and getattr(i, 'temp_connection', None)]
        logger.log(TRACE,
            f"[PURGE] step 1 — mouseGrabber={type(grabber).__name__ if grabber else 'None'} | "
            f"active_wires={len(active_wires)} | total_items={len(self.items())}"
        )
        if grabber:
            logger.log(TRACE,
                f"[PURGE] step 1 — grabber detail: type={type(grabber).__name__} "
                f"scene={grabber.scene() is not None} "
                f"parentItem={type(grabber.parentItem()).__name__ if grabber.parentItem() else 'None'}"
            )
            try:
                grabber.ungrabMouse()
                logger.log(TRACE, f"[PURGE] step 1 — ungrabMouse() called on grabber")
            except Exception as e:
                logger.warning(f"[PURGE] step 1 — ungrabMouse() raised {type(e).__name__}: {e}")

        # ── STEP 2: Floating wire cleanup ─────────────────────────────────────
        # Wires in progress that were never completed would be orphaned by the purge.
        logger.log(TRACE, f"[PURGE] step 2 — scanning for floating temp_connections")
        float_count = 0
        for item in list(self.items()):
            if isinstance(item, BaseNode) and getattr(item, 'temp_connection', None):
                logger.log(TRACE, f"[PURGE] step 2 — removing floating temp_connection from node '{getattr(item, 'title', '?')}'")
                try:
                    self.removeItem(item.temp_connection)
                    item.temp_connection = None
                    float_count += 1
                except Exception as e:
                    logger.warning(f"[PURGE] step 2 — temp_connection removal raised {type(e).__name__}: {e}")
        logger.log(TRACE, f"[PURGE] step 2 — removed {float_count} floating temp_connections")

        # ── STEP 3: Orphaned QGraphicsTextItem sweep ──────────────────────────
        # WarmNode children (emoji, title, body text) that got unparented before
        # their parent was removed float as top-level items. They look like complete
        # nodes visually but have no BaseNode backing — identified by the HealthNode
        # click spy returning type=QGraphicsTextItem with a memory address instead
        # of a title or uuid.
        logger.log(TRACE, f"[PURGE] step 3 — scanning for orphaned QGraphicsTextItem survivors")
        orphaned_text = [
            i for i in self.items()
            if isinstance(i, QGraphicsTextItem)
            and i.parentItem() is None
            and i is not self.fog_layer
        ]
        if orphaned_text:
            logger.warning(
                f"[PURGE] step 3 — {len(orphaned_text)} orphaned QGraphicsTextItem(s) found. "
                f"These are detached WarmNode children (zombie limbs). Removing."
            )
            for item in orphaned_text:
                try:
                    logger.log(TRACE, f"[PURGE] step 3 — removing orphaned text item id={str(id(item))[:8]}")
                    self.removeItem(item)
                except Exception as e:
                    logger.warning(f"[PURGE] step 3 — orphaned text removal raised {type(e).__name__}: {e}")
        else:
            logger.log(TRACE, f"[PURGE] step 3 — no orphaned QGraphicsTextItems found ✅")

        # ── STEP 4: Gather all purgeable items ───────────────────────────────
        logger.log(TRACE, f"[PURGE] step 4 — gathering purgeable items")
        items_to_purge = [
            i for i in self.items()
            if isinstance(i, (BaseNode, Connection, QGraphicsTextItem))
            and i.parentItem() is None
            and i is not self.fog_layer
        ]
        node_count = sum(1 for i in items_to_purge if isinstance(i, BaseNode))
        conn_count = sum(1 for i in items_to_purge if isinstance(i, Connection))
        text_count = sum(1 for i in items_to_purge if isinstance(i, QGraphicsTextItem))
        logger.log(TRACE,
            f"[PURGE] step 4 — gathered {len(items_to_purge)} items: "
            f"{node_count} nodes, {conn_count} connections, {text_count} text items"
        )

        # ── STEP 5: Pre-cleanup ───────────────────────────────────────────────
        # Stop animations and sever references while items are still in the scene
        # so all Qt APIs are valid. Do NOT call setGraphicsEffect(None) here —
        # doing so schedules a deferred repaint that fires after removal = ghost node.
        logger.log(TRACE, f"[PURGE] step 5 — pre-cleanup: stopping animations and severing connections")
        for item in items_to_purge:
            try:
                if isinstance(item, BaseNode):
                    if hasattr(item, 'behaviour') and item.behaviour and hasattr(item.behaviour, 'pulse_anim'):
                        item.behaviour.pulse_anim.stop()
                        logger.log(TRACE, f"[PURGE] step 5 — stopped pulse_anim for node '{getattr(item, 'title', '?')}'")
                    item.connections.clear()
                elif isinstance(item, Connection):
                    item.start_node = None
                    item.end_node = None
            except Exception as e:
                logger.warning(f"[PURGE] step 5 — pre-cleanup raised {type(e).__name__}: {e} for item {type(item).__name__}")

        # ── STEP 6: Batch removal ─────────────────────────────────────────────
        logger.log(TRACE, f"[PURGE] step 6 — batch removal of {len(items_to_purge)} items")
        removed_count = 0
        skipped_count = 0
        for item in items_to_purge:
            try:
                if item.scene():
                    self.removeItem(item)
                    removed_count += 1
                else:
                    skipped_count += 1
                    logger.log(TRACE, f"[PURGE] step 6 — skipped item already without scene: {type(item).__name__}")
            except Exception as e:
                logger.warning(f"[PURGE] step 6 — removeItem raised {type(e).__name__}: {e} for {type(item).__name__}")
        logger.log(TRACE, f"[PURGE] step 6 — removed {removed_count}, skipped {skipped_count}")

        # ── STEP 7: GC sweep ──────────────────────────────────────────────────
        # _prepare_for_removal in BaseNode severs all references on node exit.
        # Force Python to collect them now rather than on its own schedule.
        # Session switches are launch-equivalent — no stale objects should survive.
        logger.log(TRACE, f"[PURGE] step 7 — forcing GC sweep")
        try:
            collected = _gc.collect()
            logger.log(TRACE, f"[PURGE] step 7 — gc.collect() freed {collected} objects")
        except Exception as e:
            logger.warning(f"[PURGE] step 7 — gc.collect() raised {type(e).__name__}: {e}")

        # ── STEP 8: Scene invalidation ────────────────────────────────────────
        # Flush any deferred repaints queued on removed items before they fire
        # as ghost paints onto the new session.
        logger.log(TRACE, f"[PURGE] step 8 — invalidating scene cache")
        try:
            self.invalidate(self.sceneRect(), QGraphicsScene.AllLayers)
            for view in self.views():
                view.viewport().update()
            logger.log(TRACE, f"[PURGE] step 8 — scene invalidated, {len(self.views())} viewport(s) updated")
        except Exception as e:
            logger.warning(f"[PURGE] step 8 — invalidation raised {type(e).__name__}: {e}")

        # ── STEP 9: Dirty reset ───────────────────────────────────────────────
        logger.log(TRACE, f"[PURGE] step 9 — resetting dirty state")
        self.set_dirty(False)
        self.update()

        # ── POST-PURGE VERIFICATION ───────────────────────────────────────────
        survivors = [i for i in self.items() if i is not self.fog_layer]
        if survivors:
            for s in survivors:
                logger.warning(
                    f"[PURGE] ⚠ SURVIVOR after purge: type={type(s).__name__} "
                    f"parentItem={type(s.parentItem()).__name__ if s.parentItem() else 'None'} "
                    f"scene={s.scene() is not None} "
                    f"title={getattr(s, 'title', 'N/A')} "
                    f"uuid={getattr(s, 'uuid', 'N/A')}"
                )
        else:
            logger.log(TRACE, f"[PURGE] post-purge verification — scene clean ✅ (only fog layer remains)")

        logger.log(TRACE, f"[PURGE] ═══ SESSION PURGE COMPLETE ═══")

    # ─────────────────────────────────────────────────────────────────────────
    # KEYBOARD — delete and undo
    # ─────────────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        logger.info(f"[SCENE] keyPressEvent: key={event.key()} text='{event.text()}' focusItem={type(self.focusItem()).__name__ if self.focusItem() else None}")
        # Restore node deletion logic: if Backspace/Delete and not editing text, delete selected node(s)
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            focus = self.focusItem()
            from PySide6.QtWidgets import QGraphicsTextItem
            if not isinstance(focus, QGraphicsTextItem):
                # Node deletion logic (adapted from previous behavior)
                selected = [item for item in self.selectedItems() if isinstance(item, BaseNode)]
                if selected:
                    for node in selected:
                        self.removeItem(node)
                    event.accept()
                    return
        super().keyPressEvent(event)