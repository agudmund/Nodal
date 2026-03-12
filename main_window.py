#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - main_window.py primary window definition
# A minor UI for enjoying
# Built using a single shared braincell by Yours Truly and some intellectual assistance

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsView
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtCore import Qt
from graphics.scene import NodeScene
from widgets.buttons import CozyButton
from utils.logger import setup_logger

logger = setup_logger()


class NodeGraphicsView(QGraphicsView):
    """Custom graphics view with middle-mouse button panning and keyboard controls."""

    def __init__(self, scene):
        super().__init__(scene)
        self.middle_mouse_pressed = False
        self.last_pan_pos = None

    def mousePressEvent(self, event):
        """Handle mouse press - enable panning on middle button."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_pressed = True
            self.last_pan_pos = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move - pan canvas when middle button is held."""
        if self.middle_mouse_pressed and self.last_pan_pos:
            delta = event.pos() - self.last_pan_pos

            # Pan using scroll bars (standard Qt method)
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())

            self.last_pan_pos = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - disable panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            logger.info("Middle mouse button released - panning disabled")
            self.middle_mouse_pressed = False
            self.last_pan_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard input."""
        if event.key() == Qt.Key.Key_Backspace or event.key() == Qt.Key.Key_Delete:
            self.delete_selected_nodes()
        else:
            super().keyPressEvent(event)

    def delete_selected_nodes(self):
        """Delete all selected nodes from the scene."""
        selected_items = self.scene().selectedItems()
        if selected_items:
            for item in selected_items:
                self.scene().removeItem(item)
            logger.info(f"Deleted {len(selected_items)} selected node(s)")
        else:
            logger.debug("No nodes selected to delete")


class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Nodal - Note Organizer")
        self.setGeometry(100, 100, 1200, 800)

        # Set application icon
        icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar with controls
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        toolbar_layout.setSpacing(10)

        new_node_btn = CozyButton("New Node")
        new_node_btn.clicked.connect(self.create_new_node)
        toolbar_layout.addWidget(new_node_btn)
        toolbar_layout.addStretch()

        main_layout.addLayout(toolbar_layout)

        # Create graphics scene and view
        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setFocus()

        # Fit view to show all nodes with padding
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

        main_layout.addWidget(self.view)

        self.show()

    def create_new_node(self):
        """Create a new node at a default position."""
        # Get scene center or use a default offset
        center_x = 500
        center_y = 500
        self.scene.add_node(center_x, center_y, "New Node")
        logger.info("New node created")
