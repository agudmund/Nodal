#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - scene.py graphics scene management
-Handles node scene, blur effects, and background rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import ctypes
import sys
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsBlurEffect, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QTransform
from utils.theme import Theme
from graphics.node_types import WarmNode, NodeBase

def enable_blur(hwnd):
    """Enable Windows blur effect on the window (Windows only)."""
    # if sys.platform != "win32":
    #     return  # Silently skip on non-Windows platforms

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
        tint = Theme.FROST_COLOR
        # Windows expects: 0x AABBGGRR
        windows_color = (tint.alpha() << 24) | (tint.blue() << 16) | (tint.green() << 8) | tint.red()
        accent.GradientColor = windows_color
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Warning: Could not enable blur effect: {e}")

class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Only try to enable blur if we actually have a parent window
        if parent and hasattr(parent, 'winId'):
             enable_blur(parent.winId())

        self.temp_conn = None
        self.setSceneRect(-5000, -5000, 10000, 10000) # Give yourself room to roam

        # 1. THE FOG LAYER (The Blur Container)
        # This is a transparent rectangle that holds the blur effect
        self.fog_layer = QGraphicsRectItem(self.sceneRect())
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
        self.setSceneRect(0, 0, 2000, 2000)

    def add_connection(self, node_a, node_b):
        from graphics.connection import Connection
        conn = Connection(node_a, node_b)
        self.addItem(conn)
        node_a.connections.append(conn)
        node_b.connections.append(conn)
        return conn

    def add_node(self, x: float, y: float, title: str = "Node") -> 'WarmNode':
        """
        Add a node to the scene at the specified coordinates.
        Coordinates are clamped to the scene bounds (0-2000).

        Args:
            x: X coordinate (will be clamped to 0-2000)
            y: Y coordinate (will be clamped to 0-2000)
            title: Node title label

        Returns:
            WarmNode: The created and added node
        """
        # Clamp coordinates to scene bounds
        x = max(0, min(2000, x))
        y = max(0, min(2000, y))

        # Create a WarmNode with auto-incremented node_id
        node_id = len([item for item in self.items() if isinstance(item, NodeBase)])
        node = WarmNode(node_id=node_id, title=title, pos=QPointF(x, y))
        node.setZValue(10) 
        self.addItem(node)
        return node

    def drawBackground(self, painter, rect):
        bg_color = Theme.get_alpha(Theme.FROST_COLOR, Theme.CANVAS_OPACITY)
        painter.setBrush(bg_color) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

    def mousePressEvent(self, event):
        """Handle mouse press events on the scene."""
        # For now, just pass through to default handling
        # Port-based connection drawing will be implemented separately
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events on the scene."""
        # Port-based connection system will handle dragging
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events on the scene."""
        # Port-based connection system will handle finalization
        super().mouseReleaseEvent(event)