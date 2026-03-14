#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main_window.py main application window
-Frameless window with draggable toolbar and node graphics view
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from pathlib import Path
import ctypes
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QGridLayout, QWidget, QGraphicsView, QSlider, QComboBox
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QEvent, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QEasingCurve, QSize, QPoint, QRect
from graphics.scene import NodeScene, enable_blur
from widgets import CozyButton
from utils.theme import Theme
from utils.logger import setup_logger
from utils.settings import Settings
from utils.session_manager import SessionManager
from widgets.log_viewer_dialog import LogViewerDialog
from widgets.settings_dialog import SettingsDialog


logger = setup_logger()

# Windows ShowWindow flags for Aero animation
SW_MINIMIZE = 6
SW_RESTORE = 9

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
        self._current_session = None  # Track current loaded session
        self._minimize_animation = None  # Store animation group for minimize
        self._restore_animation = None   # Store animation group for restore
        self._pre_minimize_geometry = None  # Store geometry before minimizing
        self._animating = False  # Flag to prevent double animations
        self._first_show = True  # Flag to trigger fade in on first show
        self.anim = None  # Store fade in animation

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

    def open_settings_window(self):
        """Shows the internal log viewer"""
        # We keep a reference so it doesn't get garbage collected
        self.settings_window = SettingsDialog(self)
        self.settings_window.show()

    def open_log_viewer(self):
        """Shows the internal log viewer"""
        # We keep a reference so it doesn't get garbage collected
        self.log_viewer = LogViewerDialog(self)
        self.log_viewer.show()

    def _create_spacer(self):
        """Create a standard padding spacer widget."""
        spacer = QWidget()
        spacer.setFixedWidth(15)
        spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        return spacer

    def _create_blur_slider(self):
        """Create the blur intensity slider with consistent styling and connections."""
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(Theme.FROST_COLOR.alpha())
        slider.setFixedWidth(150)
        slider.setToolTip("Adjust Background Abstraction")
        slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #00d2ff;
                width: 12px;
                border-radius: 6px;
            }
        """)
        slider.valueChanged.connect(self.update_blur_intensity)
        return slider

    def _load_session_names(self):
        """Load session JSON filenames from the sessions directory."""
        sessions_dir = Path("sessions")
        if not sessions_dir.exists():
            logger.warning("Sessions directory not found")
            return []

        # Find all .json files in sessions directory
        session_files = sorted(sessions_dir.glob("*.json"))
        # Return just the filenames without extension
        return [f.stem for f in session_files]

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
        """)

        # Row 0, Col 0: Top left spacer
        grid_layout.addWidget(self._create_spacer(), 0, 0)

        # Row 0, Col 1: Top toolbar with border-bottom
        self.toolbar_container, toolbar_layout = self._create_toolbar(border_position="bottom")
        toolbar_layout.addStretch()

        # Graph selector combobox (centered)
        self.combo_graphs = QComboBox()
        self.combo_graphs.setObjectName("project_selector")

        # Populate with session names from sessions/ directory
        session_names = self._load_session_names()
        if session_names:
            self.combo_graphs.addItems(session_names)
        else:
            self.combo_graphs.addItem("No sessions found")

        self.combo_graphs.setMinimumWidth(Theme.COMBOBOX_MIN_WIDTH)

        # Apply theme-driven stylesheet
        self.combo_graphs.setStyleSheet(f"""
            QComboBox#project_selector {{
                background-color: {Theme.COMBOBOX_BG.name()};
                color: {Theme.COMBOBOX_TEXT.name()};
                border: 1px solid {Theme.COMBOBOX_BORDER.name()};
                border-radius: {Theme.COMBOBOX_BORDER_RADIUS}px;
                padding: {Theme.COMBOBOX_PADDING};
                font-family: {Theme.COMBOBOX_FONT_FAMILY};
                font-size: {Theme.COMBOBOX_FONT_SIZE}pt;
                font-weight: {Theme.COMBOBOX_FONT_WEIGHT};
            }}
            QComboBox#project_selector::drop-down {{
                border: none;
                width: {Theme.COMBOBOX_DROPDOWN_WIDTH}px;
            }}
            QComboBox#project_selector QAbstractItemView {{
                background-color: {Theme.COMBOBOX_BG_OPEN.name()};
                color: {Theme.COMBOBOX_TEXT.name()};
                border: 1px solid {Theme.COMBOBOX_BORDER.name()};
                selection-background-color: {Theme.ACCENT_SELECTED.name()};
                font-family: {Theme.COMBOBOX_FONT_FAMILY};
                font-size: {Theme.COMBOBOX_FONT_SIZE}pt;
            }}
        """)

        # Connect combobox selection change to load session
        self.combo_graphs.currentIndexChanged.connect(self.on_session_changed)

        toolbar_layout.addWidget(self.combo_graphs)

        # Save button (right after combobox)
        self.btn_save_session = CozyButton("Save")
        self.btn_save_session.clicked.connect(self.save_session)
        toolbar_layout.addWidget(self.btn_save_session)

        toolbar_layout.addStretch()
        grid_layout.addWidget(self.toolbar_container, 0, 1)

        # Row 0, Col 2: Top right spacer
        grid_layout.addWidget(self._create_spacer(), 0, 2)

        # Row 1, Col 0: Left spacer
        grid_layout.addWidget(self._create_spacer(), 1, 0)

        # Row 1, Col 1: Canvas (expands) with border
        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.centerOn(1000, 1000)
        self.view.setStyleSheet(f"border: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};")
        grid_layout.addWidget(self.view, 1, 1)

        # Row 1, Col 2: Right spacer
        grid_layout.addWidget(self._create_spacer(), 1, 2)

        # Row 2, Col 0: Bottom left spacer
        grid_layout.addWidget(self._create_spacer(), 2, 0)

        # Row 2, Col 1: Bottom toolbar with border-top
        self.bottom_toolbar_container, bottom_toolbar_layout = self._create_toolbar(border_position="top")

        # New Node button (left-aligned)
        self.btn_new_node = CozyButton("Node")
        self.btn_new_node.clicked.connect(self.create_new_node)
        bottom_toolbar_layout.addWidget(self.btn_new_node)

        # Stretch to push exit button to the right
        bottom_toolbar_layout.addStretch()

        # The Blur Intensity Slider
        self.blur_slider = self._create_blur_slider()
        bottom_toolbar_layout.insertWidget(1, self.blur_slider)

        # Settings button
        self.btn_settings = CozyButton("Setings")
        self.btn_settings.clicked.connect(self.open_settings_window)
        bottom_toolbar_layout.addWidget(self.btn_settings)

        # Wait button (minimize - left of exit)
        self.btn_wait = CozyButton("Wait")
        self.btn_wait.clicked.connect(self.minimize_with_animation)
        bottom_toolbar_layout.addWidget(self.btn_wait)

        # Exit button (right-aligned)
        self.btn_exit = CozyButton("Exid")
        self.btn_exit.clicked.connect(lambda: (self.save_session(), self.close()))
        bottom_toolbar_layout.addWidget(self.btn_exit)

        grid_layout.addWidget(self.bottom_toolbar_container, 2, 1)

        # Row 2, Col 2: Bottom right spacer
        grid_layout.addWidget(self._create_spacer(), 2, 2)

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

    def load_session(self, session_name: str):
        """Load a session by name from the sessions directory."""
        if not session_name:
            return

        filepath = SessionManager.get_session_filename(session_name)
        SessionManager.load_session(self.scene, filepath, self.view)
        self._current_session = session_name
        logger.info(f"Loaded session: {session_name}")

    def save_session(self):
        """Save the current session to its file."""
        if not self._current_session:
            logger.warning("No session loaded - nothing to save")
            return

        filepath = SessionManager.get_session_filename(self._current_session)
        SessionManager.save_session(self.scene, filepath, self.view)
        logger.info(f"Saved session: {self._current_session}")

    def on_session_changed(self, index: int):
        """Handle combobox selection change."""
        if index < 0:
            return
        session_name = self.combo_graphs.currentText()
        self.load_session(session_name)

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

    def minimize_with_animation(self):
        """Minimize window with custom shrink + fade animation."""
        if self._animating:
            return

        self._animating = True
        self._pre_minimize_geometry = self.geometry()

        logger.info("Starting custom minimize animation")

        # Stop any ongoing restore animation
        if self._restore_animation:
            self._restore_animation.stop()

        # Create parallel animation group (shrink + fade happen simultaneously)
        self._minimize_animation = QParallelAnimationGroup()

        # Animate geometry shrink (to bottom-right area, like taskbar)
        geom_anim = QPropertyAnimation(self, b"geometry")
        geom_anim.setDuration(Theme.WINDOW_ANIMATION_DURATION)
        geom_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Start from current geometry
        start_geom = self.geometry()

        # End at a small size in the bottom-right corner
        end_geom = QRect(
            start_geom.right() - 100,
            start_geom.bottom() - 100,
            50,
            50
        )

        # Add intermediate keyframes for smoother animation (9 total frames)
        geom_anim.setKeyValueAt(0.0, start_geom)
        geom_anim.setKeyValueAt(0.125, QRect(
            start_geom.x() + (start_geom.width() * 0.015),
            start_geom.y() + (start_geom.height() * 0.015),
            start_geom.width() * 0.97,
            start_geom.height() * 0.97
        ))
        geom_anim.setKeyValueAt(0.25, QRect(
            start_geom.x() + (start_geom.width() * 0.06),
            start_geom.y() + (start_geom.height() * 0.06),
            start_geom.width() * 0.88,
            start_geom.height() * 0.88
        ))
        geom_anim.setKeyValueAt(0.375, QRect(
            start_geom.right() - 175,
            start_geom.bottom() - 175,
            125,
            125
        ))
        geom_anim.setKeyValueAt(0.5, QRect(
            start_geom.right() - 150,
            start_geom.bottom() - 150,
            100,
            100
        ))
        geom_anim.setKeyValueAt(0.625, QRect(
            start_geom.right() - 137,
            start_geom.bottom() - 137,
            87,
            87
        ))
        geom_anim.setKeyValueAt(0.75, QRect(
            start_geom.right() - 125,
            start_geom.bottom() - 125,
            75,
            75
        ))
        geom_anim.setKeyValueAt(0.875, QRect(
            start_geom.right() - 112,
            start_geom.bottom() - 112,
            62,
            62
        ))
        geom_anim.setKeyValueAt(1.0, end_geom)

        # Animate opacity fade
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(Theme.WINDOW_ANIMATION_DURATION)
        opacity_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Add intermediate keyframes for smoother fade (9 total frames)
        opacity_anim.setKeyValueAt(0.0, 1.0)
        opacity_anim.setKeyValueAt(0.125, 0.875)
        opacity_anim.setKeyValueAt(0.25, 0.75)
        opacity_anim.setKeyValueAt(0.375, 0.625)
        opacity_anim.setKeyValueAt(0.5, 0.5)
        opacity_anim.setKeyValueAt(0.625, 0.375)
        opacity_anim.setKeyValueAt(0.75, 0.25)
        opacity_anim.setKeyValueAt(0.875, 0.125)
        opacity_anim.setKeyValueAt(1.0, 0.0)

        self._minimize_animation.addAnimation(geom_anim)
        self._minimize_animation.addAnimation(opacity_anim)
        self._minimize_animation.finished.connect(self._on_minimize_animation_finished)

        self._minimize_animation.start()

    def _on_minimize_animation_finished(self):
        """Called when minimize animation completes."""
        logger.info("Minimize animation finished, calling showMinimized()")
        self.showMinimized()
        self._animating = False

    def changeEvent(self, event):
        """Handle window state changes to animate restore."""
        if event.type() == QEvent.WindowStateChange:
            if not (self.windowState() & Qt.WindowMinimized) and self._pre_minimize_geometry:
                # Window is being restored from minimized state
                logger.info("Window restored, starting restore animation")
                self._animate_restore()
        super().changeEvent(event)

    def _animate_restore(self):
        """Animate window expanding and fading back in."""
        if self._animating:
            return

        self._animating = True

        # Stop any ongoing minimize animation
        if self._minimize_animation:
            self._minimize_animation.stop()

        # Reset opacity to 0 before animating back in
        self.setWindowOpacity(0.0)

        logger.info("Starting custom restore animation")

        # Create parallel animation group (expand + fade in)
        self._restore_animation = QParallelAnimationGroup()

        # Animate geometry expand back to original
        geom_anim = QPropertyAnimation(self, b"geometry")
        geom_anim.setDuration(Theme.WINDOW_RESTORE_ANIMATION_DURATION)
        geom_anim.setEasingCurve(QEasingCurve.Linear)

        current_geom = self.geometry()
        target_geom = self._pre_minimize_geometry

        # Add intermediate keyframes for smoother animation (9 total frames)
        geom_anim.setKeyValueAt(0.0, current_geom)
        geom_anim.setKeyValueAt(0.125, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.125),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.125),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.125),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.125)
        ))
        geom_anim.setKeyValueAt(0.25, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.25),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.25),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.25),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.25)
        ))
        geom_anim.setKeyValueAt(0.375, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.375),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.375),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.375),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.375)
        ))
        geom_anim.setKeyValueAt(0.5, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.5),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.5),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.5),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.5)
        ))
        geom_anim.setKeyValueAt(0.625, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.625),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.625),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.625),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.625)
        ))
        geom_anim.setKeyValueAt(0.75, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.75),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.75),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.75),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.75)
        ))
        geom_anim.setKeyValueAt(0.875, QRect(
            current_geom.x() + ((target_geom.x() - current_geom.x()) * 0.875),
            current_geom.y() + ((target_geom.y() - current_geom.y()) * 0.875),
            current_geom.width() + ((target_geom.width() - current_geom.width()) * 0.875),
            current_geom.height() + ((target_geom.height() - current_geom.height()) * 0.875)
        ))
        geom_anim.setKeyValueAt(1.0, target_geom)

        # Animate opacity fade in
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(Theme.WINDOW_RESTORE_ANIMATION_DURATION)
        opacity_anim.setEasingCurve(QEasingCurve.Linear)

        # Add intermediate keyframes for smoother fade (9 total frames)
        opacity_anim.setKeyValueAt(0.0, 0.0)
        opacity_anim.setKeyValueAt(0.125, 0.125)
        opacity_anim.setKeyValueAt(0.25, 0.25)
        opacity_anim.setKeyValueAt(0.375, 0.375)
        opacity_anim.setKeyValueAt(0.5, 0.5)
        opacity_anim.setKeyValueAt(0.625, 0.625)
        opacity_anim.setKeyValueAt(0.75, 0.75)
        opacity_anim.setKeyValueAt(0.875, 0.875)
        opacity_anim.setKeyValueAt(1.0, 1.0)

        self._restore_animation.addAnimation(geom_anim)
        self._restore_animation.addAnimation(opacity_anim)
        self._restore_animation.finished.connect(lambda: setattr(self, '_animating', False))

        self._restore_animation.start()

    def showEvent(self, event):
        """Triggered when the window is first shown to the user."""
        super().showEvent(event)

        # Fade in on first show
        if self._first_show:
            self._first_show = False
            self.setWindowOpacity(0.0)
            self.anim = QPropertyAnimation(self, b"windowOpacity")
            self.anim.setDuration(600)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim.start()

        # Force a 'First Sync' of the blur layer so it's not 
        # trying to blur the infinite void on frame one.
        self.update_blur_intensity(self.blur_slider.value())

    def closeEvent(self, event):
        # 1. Save Geometry immediately while the window is still valid
        if Settings.get_bool("interface/restore_geom", True):
            Settings.set_window_geometry(self.saveGeometry())
            logger.debug("Geometry saved to nodal_config.ini")

        # 2. Check if we are already fading out
        # If the opacity is already 0, we've finished the animation
        if self.windowOpacity() <= 0.0:
            event.accept()
            return

        # 3. Ignore the initial close request to allow the animation to play
        event.ignore()

        # 4. Start the Fade-Out Animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.windowOpacity())
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        
        # 5. When the animation finishes, THEN call the real close
        self.anim.finished.connect(self.close) 
        self.anim.start()