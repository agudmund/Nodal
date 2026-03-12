#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main_window.py main application window
-Frameless window with draggable toolbar and node graphics view
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt
from graphics.scene import NodeScene, enable_blur
from widgets import CozyButton
from utils.theme import Theme
from utils.logger import setup_logger

logger = setup_logger()

class NodeGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.middle_mouse_pressed = False
        self.last_pan_pos = None
        self.alt_right_pressed = False
        self.last_zoom_pos = None
        self.zoom_speed = 0.002  # Sensitivity for zoom (adjust as needed)
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_zoom = 1.0
        self.viewport().setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    def mousePressEvent(self, event):
        # Alt + Right Mouse Button = Zoom mode
        if event.modifiers() == Qt.KeyboardModifier.AltModifier and event.button() == Qt.MouseButton.RightButton:
            self.alt_right_pressed = True
            self.last_zoom_pos = event.pos()
            self.setCursor(Qt.SizeVerCursor)
            event.accept()
        # Middle Mouse Button = Pan mode
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_pressed = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.SizeAllCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Zoom mode: Alt + Right Mouse drag
        if self.alt_right_pressed and self.last_zoom_pos:
            delta_y = event.pos().y() - self.last_zoom_pos.y()
            # Drag up = positive delta = zoom in
            # Drag down = negative delta = zoom out
            zoom_factor = 1.0 + (delta_y * self.zoom_speed)
            zoom_factor = max(self.min_zoom / self.current_zoom, min(self.max_zoom / self.current_zoom, zoom_factor))

            self.scale(zoom_factor, zoom_factor)
            self.current_zoom *= zoom_factor
            self.last_zoom_pos = event.pos()
            event.accept()
        # Pan mode: Middle Mouse drag
        elif self.middle_mouse_pressed and self.last_pan_pos:
            delta = event.pos() - self.last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_pos = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.alt_right_pressed:
            self.alt_right_pressed = False
            self.last_zoom_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        elif self.middle_mouse_pressed:
            self.middle_mouse_pressed = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.handle_height = 70
        self._dragging_window = False
        self._drag_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        enable_blur(int(self.winId()))

    def init_ui(self):
        self.setWindowTitle("Nodal")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Draggable Toolbar Container (Top)
        self.toolbar_container = QWidget()
        self.toolbar_container.setFixedHeight(self.handle_height)
        self.toolbar_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-bottom: 1px solid {Theme.TOOLBAR_BORDER.name()};
        """)

        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(15, 0, 15, 0)
        toolbar_layout.addStretch()

        main_layout.addWidget(self.toolbar_container)

        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.centerOn(1000, 1000)
        main_layout.addWidget(self.view)

        # Bottom Toolbar Container
        self.bottom_toolbar_container = QWidget()
        self.bottom_toolbar_container.setFixedHeight(self.handle_height)
        self.bottom_toolbar_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-top: 1px solid {Theme.TOOLBAR_BORDER.name()};
        """)

        bottom_toolbar_layout = QHBoxLayout(self.bottom_toolbar_container)
        bottom_toolbar_layout.setContentsMargins(15, 0, 15, 0)

        # New Node button (left-aligned)
        new_node_btn = CozyButton("New Node")
        new_node_btn.clicked.connect(self.create_new_node)
        bottom_toolbar_layout.addWidget(new_node_btn)

        # Stretch to push exit button to the right
        bottom_toolbar_layout.addStretch()

        # Exit button (right-aligned)
        exit_btn = CozyButton("Exit")
        exit_btn.clicked.connect(self.close)
        bottom_toolbar_layout.addWidget(exit_btn)

        main_layout.addWidget(self.bottom_toolbar_container)

        self.show()

    def create_new_node(self):
        view_center = self.view.mapToScene(self.view.viewport().width() // 2, self.view.viewport().height() // 2)
        self.scene.add_node(view_center.x(), view_center.y(), "New Node")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < self.handle_height:
            self._dragging_window = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_window:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + (new_pos - self._drag_pos))
            self._drag_pos = new_pos
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging_window = False
        super().mouseReleaseEvent(event)