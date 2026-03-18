#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - scene.py graphics scene management
-Handles node scene, blur effects, and background rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import ctypes
import sys
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsBlurEffect, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QTransform
from .Theme import Theme
from utils.motivational_messages import MOTIVATIONAL_MESSAGES
from .BaseNode import BaseNode
from .WarmNode import WarmNode

def enable_blur(hwnd):
    """Enable Windows blur effect on the window (Windows only)."""
    if sys.platform != "win32":
        return  # Silently skip on non-Windows platforms

    if not hwnd or sys.platform != "win32":
        return

    try:
        class WindowCompositionAttributeData(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p), ("SizeOfData", ctypes.c_size_t)]
        class AccentPolicy(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int), 
                        ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]

        accent = AccentPolicy()
        # Change the AccentState to 5 for Mica
        # And we need to add a "Flag" to tell Windows we want to use our own tint
        # In scene.py -> enable_blur 
        accent.AccentState = 5  # Keep Mica
        accent.AccentFlags = 0  # Tell Windows to stay out of the tinting business
        accent.GradientColor = 0x00000000 # Fully transparent
        data = WindowCompositionAttributeData() 
        data.Attribute = 19 
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        # Convert QColor to a Windows-friendly Hex (ABGR format)
        tint = Theme.frostColor
        # Windows expects: 0x AABBGGRR
        windows_color = (tint.alpha() << 24) | (tint.blue() << 16) | (tint.green() << 8) | tint.red()
        accent.GradientColor = windows_color
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Warning: Could not enable blur effect: {e}")

class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dirty = False
        self._undo_stack = []       # Each entry: list of (node_dict, [conn_dicts]) for one delete action
        self._undo_max = 30         # Cap memory use — oldest actions fall off the back

        # Only try to enable blur if we actually have a parent window
        if parent and hasattr(parent, 'winId'):
             enable_blur(parent.winId())

        self.temp_conn = None
        self.setSceneRect(-1000, -1000, 1000, 1000) # Give yourself room to roam

        # 1. THE FOG LAYER (The Blur Container)
        # This is a transparent rectangle that holds the blur effect
        self.fog_layer = QGraphicsRectItem(self.sceneRect())
        self.fog_layer.setRect(-1000, -1000, 1000, 1000)
        self.fog_layer.setBrush(Qt.NoBrush)
        self.fog_layer.setPen(Qt.NoPen)
        self.fog_layer.setZValue(-100) # Deep in the background
        
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint) # Faster for slider-dragging
        self.fog_layer.setGraphicsEffect(self.blur_effect)
        

        # Apply the effect to the LAYER, not the view
        self.blur_effect = QGraphicsBlurEffect()
        self.fog_layer.setGraphicsEffect(self.blur_effect)
        self.addItem(self.fog_layer)

    def set_dirty(self, value: bool):
        """Updates the dirty state and could eventually trigger UI changes."""
        if self._dirty != value:
            self._dirty = value
            # logger.debug(f"Scene Accountability: Dirty Flag set to {value}")
            # Here is where you'd eventually tell the Save Button to glow!

    def is_dirty(self):
        return self._dirty

    def get_session_data(self) -> dict:
        """Gather all nodes and connections for session persistence.

        Returns:
            Dictionary with version, serialized nodes, and connection metadata.
        """
        # 1. Gather Nodes (Existing)
        nodes_data = [item.to_dict() for item in self.items() if isinstance(item, BaseNode)]

        # 2. Gather Connections (The New Nerve Ledger)
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

    def add_connection(self, node_a, node_b):
        """Create and register a connection (wire) between two nodes.

        Args:
            node_a: Source BaseNode
            node_b: Target BaseNode

        Returns:
            Connection instance
        """
        conn = Connection(node_a, node_b)
        self.addItem(conn)
        node_a.connections.append(conn)
        node_b.connections.append(conn)
        return conn

    def add_node(self, x: float, y: float, title: str = None) -> 'WarmNode':
        """Create and add a WarmNode to the scene.

        Automatically generates a node_id based on existing node count.
        Uses random motivational message as title if not provided.

        Args:
            x: Scene X coordinate
            y: Scene Y coordinate
            title: Optional node title (uses random motivational message if None)

        Returns:
            Newly created and added WarmNode instance
        """

        # Use random motivational message if no title provided
        if title is None:
            title = random.choice(MOTIVATIONAL_MESSAGES)

        # Create a WarmNode with auto-incremented node_id
        node_id = len([item for item in self.items() if isinstance(item, BaseNode)])
        node = WarmNode(node_id=node_id, title=title, pos=QPointF(x, y))
        node.setZValue(10) 
        self.addItem(node)
        return node

    def clear_nodes(self):
        """Remove all nodes from the scene while preserving the background fog layer.
        Properly cleans up graphics effects and invalidates the scene cache.
        """
        # 1. Grab everything currently on the stage
        all_items = self.items()
        
        # 2. THE ULTIMATUM: If it's not the Fog, it's gone.
        # This catches nodes, wires, ports, and 'Ghost' artifacts.
        for item in all_items:
            if item != self.fog_layer:
                # Strip effects (like shadows) before removal to clear the buffer
                if hasattr(item, 'setGraphicsEffect'):
                    item.setGraphicsEffect(None)
                self.removeItem(item)

        # 3. THE GHOST BUSTER: Invalidate the entire visual cache
        # This is the 'Simulate pointing at every pixel' button in code.
        self.invalidate(self.sceneRect(), QGraphicsScene.AllLayers)
        
        # 4. Notify the cameras
        for view in self.views():
            view.viewport().update()

    def rebuild_from_session(self, data: dict):
        """Reconstruct scene nodes and connections from session data.
        Clears existing nodes and rebuilds graph from serialized state.

        Args:
            data: Dictionary with 'nodes' and 'connections' lists from session
        """
        # from graphics import node_types
        from graphics.Connection import Connection

        self.clear_nodes()
        node_map = {} # To keep track of UUIDs during the build

        # 1. First Pass: Create all Nodes
        for node_data in data.get("nodes", []):
            new_node = BaseNode.from_dict(node_data)
            self.addItem(new_node)
            node_map[new_node.uuid] = new_node

        # 2. Second Pass: Re-plug the Nerves
        for conn_data in data.get("connections", []):
            start_node = node_map.get(conn_data.get("start_node_uuid"))
            end_node = node_map.get(conn_data.get("end_node_uuid"))

            if start_node and end_node:
                new_conn = Connection(start_node, end_node)
                self.addItem(new_conn)

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

    def drawBackground(self, painter, rect):
        bg_color = Theme.get_alpha(Theme.frostColor, Theme.frostColor.alpha())
        painter.setBrush(bg_color) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)