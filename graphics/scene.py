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
from .theme import Theme
from utils.motivational_messages import MOTIVATIONAL_MESSAGES
from .BaseNode import BaseNode
from .node_types import WarmNode

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
        # 1. Gather Nodes (Existing)
        nodes_data = [item.to_dict() for item in self.items() if isinstance(item, BaseNode)]
        
        # 2. Gather Connections (The New Nerve Ledger)
        from graphics.connection import Connection
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
        from graphics.connection import Connection
        conn = Connection(node_a, node_b)
        self.addItem(conn)
        node_a.connections.append(conn)
        node_b.connections.append(conn)
        return conn

    def add_node(self, x: float, y: float, title: str = None) -> 'WarmNode':
        """
        Add a node to the scene at the specified coordinates.
        Coordinates are clamped to the scene bounds (0-2000).

        Args:
            x: X coordinate
            y: Y coordinate
            title: Node title label (if None, selects random motivational message)

        Returns:
            WarmNode: The created and added node
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
        """
        PURPOSE: Clear the stage of all transient characters.
        CLAIM: Only the Fog Layer has a permanent claim to existing.
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
        from graphics import node_types
        from graphics.connection import Connection # The Nerve specialist

        self.clear_nodes()
        node_map = {} # To keep track of UUIDs during the build

        # 1. First Pass: Create all Nodes
        for node_data in data.get("nodes", []):
            node_type = node_data.get("type", "warm")
            # ... (your existing factory logic) ...
            new_node = node_types.WarmNode.from_dict(node_data)
            self.addItem(new_node)
            node_map[new_node.uuid] = new_node

        # 2. Second Pass: Re-plug the Nerves
        for conn_data in data.get("connections", []):
            start_node = node_map.get(conn_data.get("start_node_uuid"))
            end_node = node_map.get(conn_data.get("end_node_uuid"))
            
            if start_node and end_node:
                new_conn = Connection(start_node, end_node)
                self.addItem(new_conn)

    def drawBackground(self, painter, rect):
        bg_color = Theme.get_alpha(Theme.frostColor, Theme.frostColor.alpha())
        painter.setBrush(bg_color) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)


        