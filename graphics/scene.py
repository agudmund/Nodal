import ctypes
import sys
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from utils.theme import Theme
from graphics.node import Node

def enable_blur(hwnd):
    """Enable Windows blur effect on the window (Windows only)."""
    if sys.platform != "win32":
        return  # Silently skip on non-Windows platforms

    try:
        class WindowCompositionAttributeData(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p), ("SizeOfData", ctypes.c_size_t)]
        class AccentPolicy(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int), 
                        ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]

        accent = AccentPolicy()
        accent.AccentState = 3 
        data = WindowCompositionAttributeData()
        data.Attribute = 19 
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Warning: Could not enable blur effect: {e}")

class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 2000)

    def add_node(self, x: float, y: float, title: str = "Node") -> Node:
        """
        Add a node to the scene at the specified coordinates.
        Coordinates are clamped to the scene bounds (0-2000).

        Args:
            x: X coordinate (will be clamped to 0-2000)
            y: Y coordinate (will be clamped to 0-2000)
            title: Node title label

        Returns:
            Node: The created and added node
        """
        # Clamp coordinates to scene bounds
        x = max(0, min(2000, x))
        y = max(0, min(2000, y))

        node = Node(x, y, title)
        node.setZValue(10) 
        self.addItem(node)
        return node

    def drawBackground(self, painter, rect):
        painter.setBrush(Theme.FROST_COLOR) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)