#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main_window.py main application window
-Frameless window with draggable toolbar and node graphics view
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QGridLayout, QWidget, QGraphicsView, QSlider
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt
from graphics.scene import NodeScene, enable_blur
from widgets import CozyButton
from utils.theme import Theme
from utils.logger import setup_logger

logger = setup_logger()

class NodeGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        
        # --- Internal Navigation State ---
        self.middle_mouse_pressed = False
        self.last_pan_pos = None
        self.alt_right_pressed = False
        self.last_zoom_pos = None
        self.zoom_speed = 0.002
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_zoom = 1.0

        # --- Transparency & Rendering ---
        # 1. This tells the widget itself to be see-through
        self.viewport().setAttribute(Qt.WA_TranslucentBackground)

        # 2. Remove frame and set transparent background
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setStyleSheet("background: transparent;")

        # 3. Optimization: Force full updates so the blur doesn't leave 'ghosts'
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        """Mouse wheel zoom - scroll up to zoom in, scroll down to zoom out."""
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.apply_zoom(zoom_factor)

    def apply_zoom(self, factor):
        """Apply zoom with bounds checking."""
        new_zoom = self.current_zoom * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.current_zoom = new_zoom

    def drawBackground(self, painter, rect):
        """
        The physical 'Glass' layer. 
        It draws the tint and the grain texture OVER the Mica blur.
        """
        painter.save()
        
        # Keep the grain/tint static relative to the window (don't move when panning)
        painter.setWorldTransform(painter.worldTransform().inverted()[0] * painter.worldTransform())
        
        # 1. THE OBSIDIAN TINT
        # Responsive to Theme.FROST_COLOR.alpha() (The Slider!)
        painter.fillRect(self.viewport().rect(), Theme.FROST_COLOR)
        
        # 2. THE DIFFUSER GRAIN
        # This provides the 'fixed focal point' that makes the blur look professional
        alpha = Theme.FROST_COLOR.alpha()
        if alpha > 10:
            # Subtle white 'sandblasted' grain
            painter.setBrush(QBrush(QColor(255, 255, 255, 5), Qt.Dense7Pattern))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.viewport().rect())
            
            # Subtle black depth grain
            painter.setBrush(QBrush(QColor(0, 0, 0, 3), Qt.Dense7Pattern))
            painter.drawRect(self.viewport().rect())
        
        painter.restore()

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
            self.apply_zoom(zoom_factor)
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
        self.handle_height = Theme.HANDLE_HEIGHT
        self._dragging_window = False
        self._drag_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        enable_blur(int(self.winId()))

    def _create_toolbar(self, border_position="bottom"):
        """
        Create a toolbar container with consistent styling.

        Args:
            border_position: "top", "bottom", or None for no border

        Returns:
            tuple: (container QWidget, layout QHBoxLayout)
        """
        container = QWidget()
        container.setFixedHeight(self.handle_height)

        border_style = ""
        if border_position:
            border_style = f"border-{border_position}: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"

        container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            {border_style}
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 0, 15, 0)

        return container, layout

    def init_ui(self):
        self.setWindowTitle("Nodal")
        self.setGeometry(100, 100, 1200, 800)

        # Main central widget with grid layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Theme.WINDOW_BG.name()};
                border: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            }}
            #Toolbar {{
                background-color: {Theme.TOOLBAR_BG.name()};
                border-bottom: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            }}
        """)

        # Row 0, Col 0: Top left spacer (empty, no border)
        top_left_spacer = QWidget()
        top_left_spacer.setFixedWidth(15)
        top_left_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(top_left_spacer, 0, 0)

        # Row 0, Col 1: Top toolbar with border-bottom
        self.toolbar_container, toolbar_layout = self._create_toolbar(border_position="bottom")
        toolbar_layout.addStretch()
        grid_layout.addWidget(self.toolbar_container, 0, 1)

        # Row 0, Col 2: Top right spacer (empty, no border)
        top_right_spacer = QWidget()
        top_right_spacer.setFixedWidth(15)
        top_right_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(top_right_spacer, 0, 2)

        # Row 1, Col 0: Left spacer (padding only)
        left_spacer = QWidget()
        left_spacer.setFixedWidth(15)
        left_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(left_spacer, 1, 0)

        # Row 1, Col 1: Canvas (expands) with border
        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.centerOn(1000, 1000)
        self.view.setStyleSheet(f"border: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};")
        grid_layout.addWidget(self.view, 1, 1)

        # Row 1, Col 2: Right spacer (padding only)
        right_spacer = QWidget()
        right_spacer.setFixedWidth(15)
        right_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(right_spacer, 1, 2)

        # Row 2, Col 0: Bottom left spacer (empty, no border)
        bottom_left_spacer = QWidget()
        bottom_left_spacer.setFixedWidth(15)
        bottom_left_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(bottom_left_spacer, 2, 0)

        # Row 2, Col 1: Bottom toolbar with border-top
        self.bottom_toolbar_container, bottom_toolbar_layout = self._create_toolbar(border_position="top")

        # New Node button (left-aligned)
        self.btn_new_node = CozyButton("New Node")
        self.btn_new_node.clicked.connect(self.create_new_node)
        bottom_toolbar_layout.addWidget(self.btn_new_node)

        # Stretch to push exit button to the right
        bottom_toolbar_layout.addStretch()

        # The Blur Intensity Slider
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(0, 255)
        self.blur_slider.setValue(Theme.FROST_COLOR.alpha())
        self.blur_slider.setFixedWidth(150)
        self.blur_slider.setToolTip("Adjust Background Abstraction")
        self.blur_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #00d2ff;
                width: 12px;
                border-radius: 6px;
            }
        """)
        self.blur_slider.valueChanged.connect(self.update_blur_intensity)

        # Add it to your layout (between the buttons)
        bottom_toolbar_layout.insertWidget(1, self.blur_slider)

        # Exit button (right-aligned)
        self.btn_exit = CozyButton("Exit")
        self.btn_exit.clicked.connect(self.close)
        bottom_toolbar_layout.addWidget(self.btn_exit)

        grid_layout.addWidget(self.bottom_toolbar_container, 2, 1)

        # Row 2, Col 2: Bottom right spacer (empty, no border)
        bottom_right_spacer = QWidget()
        bottom_right_spacer.setFixedWidth(15)
        bottom_right_spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        grid_layout.addWidget(bottom_right_spacer, 2, 2)

        # Set row/column stretch to make canvas expandable
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnStretch(1, 1)

        self.show()

    def update_blur_intensity(self, value):
        Theme.FROST_COLOR.setAlpha(value)

        # Map the blur (Sane range 0-30 for performance)
        blur_radius = (value / 255) * 30

        # Update the fog layer to what the user actually sees
        visible_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        self.scene.fog_layer.setRect(visible_rect)

        self.blur_slider.setToolTip(f"Optimized Smudge: {int(blur_radius)}px")
        self.view.viewport().update()

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
        super().mouseMoveEvent(event)
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

    def showEvent(self, event):
        """Triggered when the window is first shown to the user."""
        super().showEvent(event)
        # Force a 'First Sync' of the blur layer so it's not 
        # trying to blur the infinite void on frame one.
        self.update_blur_intensity(self.blur_slider.value())