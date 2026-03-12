#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - main_window.py primary window definition
# A minor UI for enjoying
# Built using a single shared braincell by Yours Truly and some intellectual assistance

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QGraphicsView
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtCore import Qt
from graphics.scene import NodeScene
from utils.logger import setup_logger

logger = setup_logger()


class NodeGraphicsView(QGraphicsView):
    """Custom graphics view with middle-mouse button panning."""

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
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create graphics scene and view
        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Fit view to show all nodes with padding
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

        layout.addWidget(self.view)

        self.show()
