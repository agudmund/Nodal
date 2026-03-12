#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - scene.py graphics scene for nodes
# Manages the canvas and all node items

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from graphics.node import Node


class NodeScene(QGraphicsScene):
    """
    Custom graphics scene with grid background and node management.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Scene settings
        self.setSceneRect(0, 0, 2000, 2000)
        self.grid_size = 20
        self.grid_color = QColor(200, 200, 200, 50)

        # Add some example nodes to start
        self.add_node(100, 100, "Input")
        self.add_node(400, 100, "Process")
        self.add_node(250, 300, "Output")

    def add_node(self, x: float, y: float, title: str = "Node") -> Node:
        """
        Add a new node to the scene.

        Args:
            x: X position
            y: Y position
            title: Node title/label

        Returns:
            Node: The created node
        """
        node = Node(x, y, title)
        self.addItem(node)
        return node
