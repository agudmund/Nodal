#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main_window.py main application window
-Frameless window with draggable toolbar and node graphics view
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QGridLayout, QWidget, QGraphicsView, QSlider, QComboBox, QGraphicsScene
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QTransform
from PySide6.QtCore import Qt, QEvent, QTimer, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QEasingCurve, QSize, QPoint, QRect
from graphics.Scene import NodeScene, enable_blur
from graphics.Theme import Theme
from widgets import CozyButton
from utils.logger import setup_logger
from utils.settings import Settings
from utils.session_manager import SessionManager
from utils.window_animator import WindowAnimator
from widgets.log_viewer_dialog import LogViewerDialog
from widgets.settings_dialog import SettingsDialog
from widgets.demo_dialog import DemoDialog


logger = setup_logger()

# Windows ShowWindow flags for Aero animation
SW_MINIMIZE = 6
SW_RESTORE = 9

class NodeGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        # --- 1. THE FOUNDATION (Ledger & Anchors) ---
        self._first_interact_done = False
        self.viewport_locked = False
        self.setInteractive(True)
        
        # Stop Qt from trying to 'help' with placement
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setSceneRect(-5000, -5000, 10000, 10000)

        # --- 2. KILL THE FRAME (The Zero-Point Directive) ---
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.viewport().setContentsMargins(0, 0, 0, 0)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- 3. THE NAVIGATOR (Internal State) ---
        self.current_zoom = 1.0
        self.zoom_speed = 0.002
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Consolidate: use underscore naming for internal mouse state
        self._last_pan_pos = None 
        self._last_zoom_pos = None
        self._alt_right_pressed = False

        # --- 4. THE MICA CORE (Transparency & Quality) ---
        # Use a BspTree to make finding nodes faster in a large scene
        self.scene().setItemIndexMethod(QGraphicsScene.BspTreeIndex)

        self.viewport().setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState)
        try:
            self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustCursorShape)
        except AttributeError:
            pass
        self.setRenderHint(QPainter.Antialiasing)

    def wheelEvent(self, event):
        """
        PURPOSE: Provide stepped zooming via the mouse wheel.
        ACCOUNTABILITY: zoom_factor is relative. No cache update needed as the 
        ledger will be naturally captured during the next save.
        """
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.apply_zoom(zoom_factor)
        # The cache call is removed because the Ledger is the only truth now.

    def apply_zoom(self, factor):
        new_zoom = self.current_zoom * factor

        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.current_zoom = new_zoom

            # Update the HUD
            if hasattr(self.window(), 'debug_label'):
                self.window().debug_label.setText(f"Zoom: {self.current_zoom:.2f}x")

        if hasattr(self.window(), 'view_zoom'):
            self.window().view_zoom = self.current_zoom

    def drawBackground(self, painter, rect):
        painter.save()
        painter.resetTransform()

        # 1. THE OBSIDIAN TINT (Always fast)
        painter.fillRect(self.viewport().rect(), Theme.frostColor)

        # 2. THE DIFFUSER GRAIN (The Optimization)
        alpha = Theme.frostColor.alpha()
        # Skip grain if it's too faint or if we are zoomed out too far 
        # to maintain high-performance Mica feel.
        if alpha > 10 and self.current_zoom > 0.2:
            painter.setBrush(QBrush(QColor(255, 255, 255, 5), Qt.Dense7Pattern))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.viewport().rect())
            
            painter.setBrush(QBrush(QColor(0, 0, 0, 3), Qt.Dense7Pattern))
            painter.drawRect(self.viewport().rect())
        
        painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            # ACCOUNTABILITY: We use position() for sub-pixel accuracy.
            self._last_pan_pos = event.position() 
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return # Skip super() to prevent the 'Camera Operator' from flinching
        
        

        # Alt + Right Mouse Button = Zoom mode
        if event.modifiers() == Qt.KeyboardModifier.AltModifier and event.button() == Qt.MouseButton.RightButton:
            self._alt_right_pressed = True
            self.last_zoom_pos = event.pos()
            self.setCursor(Qt.SizeVerCursor)
            event.accept()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Don't process pan/zoom during viewport restoration to prevent interference
        if self.viewport_locked:
            event.accept()
            return

        # Zoom mode: Alt + Right Mouse drag
        if self._alt_right_pressed and self.last_zoom_pos:
            delta_y = event.pos().y() - self.last_zoom_pos.y()
            # Drag up = positive delta = zoom in
            # Drag down = negative delta = zoom out
            zoom_factor = 1.0 + (delta_y * self.zoom_speed)
            self.apply_zoom(zoom_factor)
            self.last_zoom_pos = event.pos()
            event.accept()

        if event.buttons() & Qt.MouseButton.MiddleButton:
            curr_pos = event.position() # High-precision float point
            
            # --- THE SOFT-SYNC GUARD ---
            if not self._first_interact_done:
                self.centerOn(self.window().view_pan_x, self.window().view_pan_y)
                self._last_pan_pos = curr_pos
                self._first_interact_done = True
                event.accept()
                return

            # Calculate delta using high-precision floats
            # QPointF - QPointF = QPointF
            delta = curr_pos - self._last_pan_pos
            self._last_pan_pos = curr_pos

            zoom = self.transform().m11()
            
            # Update the Ledger with the exact fractional movement
            self.window().view_pan_x -= delta.x() / zoom
            self.window().view_pan_y -= delta.y() / zoom

            # Enforce the absolute reality
            self.centerOn(self.window().view_pan_x, self.window().view_pan_y)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        PURPOSE: Reset the cursor and state when the interaction ends.
        ACCOUNTABILITY: We remove the _update_viewport_cache call. It has no 
        claim to existing in a Ledger-based world.
        """
        if self._alt_right_pressed:
            self._alt_right_pressed = False
            self._last_zoom_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
            event.accept()

        super().mouseReleaseEvent(event)
           

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Delete selected nodes
            self.delete_selected_nodes()
            event.accept()
        else:
            super().keyPressEvent(event)

    def delete_selected_nodes(self):
        """Delete all selected BaseNode instances from the scene.
        Filters for BaseNode types to exclude other graphics items. Updates viewport.
        """
        scene = self.scene()
        if not scene:
            return

        # Get all selected items
        selected_items = scene.selectedItems()

        # Filter for nodes only (exclude other graphics items)
        nodes_to_delete = [item for item in selected_items if isinstance(item, BaseNode)]

        # Remove each node
        for node in nodes_to_delete:
            scene.removeItem(node)

        # Refresh viewport immediately to show deletion without lag
        if nodes_to_delete:
            self.viewport().update()


class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self._last_saved_viewport = (0.0, 0.0, 1.0)
        self.view_pan_x = 0.0
        self.view_pan_y = 0.0
        self.view_zoom = 1.0

        self.handle_height_top = Theme.handleHeightTop
        self._dragging_window = False
        self._drag_pos = None
        self._current_session = None  # Track current loaded session
        self._animator = WindowAnimator()  # Manages minimize/restore animations
        self._first_show = True  # Flag to trigger fade in on first show
        self.anim = None  # Store fade in animation

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        enable_blur(int(self.winId()))

    # Example for a Panning function in MainWindow
    def pan_view(self, delta_x, delta_y):
        self.view_pan_x += delta_x
        self.view_pan_y += delta_y
        self.view.centerOn(self.view_pan_x, self.view_pan_y)

    def _create_toolbar(self, border_position="bottom", height=None):
        """
        Create a toolbar container with consistent styling.

        Args:
            border_position: "top", "bottom", or None for no border
            height: Fixed height of the toolbar. Defaults to handleHeightTop if None.

        Returns:
            tuple: (container QWidget, layout QHBoxLayout)
        """
        container = QWidget()
        if height is None:
            height = Theme.handleHeightTop
        container.setFixedHeight(height)

        border_style = ""
        if border_position:
            border_style = f"border-{border_position}: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"

        container.setStyleSheet(f"""
            background-color: {Theme.toolbarBg.name()};
            {border_style}
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 0, 15, 0)

        return container, layout

    def open_settings_window(self):
        """Open the application settings dialog."""
        # We keep a reference so it doesn't get garbage collected
        self.settings_window = SettingsDialog(self)
        self.settings_window.show()

    def open_demo_window(self):
        """Open the proof-of-concept demo dialog."""
        # We keep a reference so it doesn't get garbage collected
        self.demo_window = DemoDialog(self)
        self.demo_window.show()

    def open_log_viewer(self):
        """Open the application log viewer dialog."""
        # We keep a reference so it doesn't get garbage collected
        self.log_viewer = LogViewerDialog(self)
        self.log_viewer.show()

    def _create_spacer(self):
        """Create a standard padding spacer widget.

        Note: The background color is baked into the stylesheet at construction time.
        This is intentional—the application does not support dynamic theme switching,
        and we are well aware of the visual appearance. If dynamic theming is needed
        in the future, this would need refactoring to use palette-based coloring.
        """
        spacer = QWidget()
        spacer.setFixedWidth(15)
        spacer.setStyleSheet(f"background-color: {Theme.windowBg.name()};")
        return spacer

    def _create_blur_slider(self):
        """Create the blur intensity slider with consistent styling and connections."""
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(Theme.frostColor.alpha())
        slider.setFixedWidth(150)
        slider.setToolTip("Adjust Background Abstraction")

        # Build slider stylesheet with optional custom handle image
        handle_style = ""
        if Theme.sliderHandleImage:
            import os
            if os.path.exists(Theme.sliderHandleImage):
                # Use custom image - convert path to URL format for stylesheet
                image_path = Theme.sliderHandleImage.replace("\\", "/")
                handle_style = f"""
            QSlider::handle:horizontal {{
                background-image: url({image_path});
                background-repeat: no-repeat;
                background-position: center;
                width: 16px;
                height: 16px;
                margin: -5px 0px;
            }}"""
            else:
                # Image path specified but file not found - fallback to solid color
                logger.warning(f"Slider handle image not found: {Theme.sliderHandleImage}, using solid color")
                handle_style = """
            QSlider::handle:horizontal {
                background: #00d2ff;
                width: 12px;
                border-radius: 6px;
                margin: -3px 0px;
            }"""
        else:
            # No image path specified - use solid color
            handle_style = """
            QSlider::handle:horizontal {
                background: #00d2ff;
                width: 12px;
                border-radius: 6px;
                margin: -3px 0px;
            }"""

        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: transparent;
                border: none;
                height: 6px;
            }}{handle_style}
        """)
        slider.valueChanged.connect(self.update_blur_intensity)
        return slider

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
                background-color: {Theme.windowBg.name()};
                border: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};
            }}
        """)

        # Row 0, Col 0: Top left spacer
        grid_layout.addWidget(self._create_spacer(), 0, 0)

        # Row 0, Col 1: Top toolbar with border-bottom
        self.toolbar_container, self.toolbar_layout = self._create_toolbar(border_position="bottom", height=Theme.handleHeightTop)

        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.setup_project_selector())
        self.toolbar_layout.addStretch()

        # Viewport position label (top right)
        from PySide6.QtWidgets import QLabel
        self.debug_label = QLabel("Y: 0")
        self.debug_label.setText("Zoom: 1.00x")
        self.debug_label.setStyleSheet("color: rgba(255, 255, 255, 150); font-family: 'Consolas';")
        
        self.toolbar_layout.addWidget(self.debug_label)

        grid_layout.addWidget(self.toolbar_container, 0, 1)

        # Row 0, Col 2: Top right spacer
        grid_layout.addWidget(self._create_spacer(), 0, 2)

        # Row 1, Col 0: Left spacer
        grid_layout.addWidget(self._create_spacer(), 1, 0)

        # Row 1, Col 1: Canvas (expands) with border
        self.scene = NodeScene()
        # main_window.py -> MainWindow.init_ui
        self.view = NodeGraphicsView(self.scene)
        # Force the 'Example.py' level of reliability:
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.view.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.view.setResizeAnchor(QGraphicsView.NoAnchor)

        # Initialize Ledger
        self.view_pan_x = 0.0
        self.view_pan_y = 0.0
        self.view_zoom = 1.0

        self.view.setStyleSheet(f"border: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};")
        grid_layout.addWidget(self.view, 1, 1)

        # Row 1, Col 2: Right spacer
        grid_layout.addWidget(self._create_spacer(), 1, 2)

        # Row 2, Col 0: Bottom left spacer
        grid_layout.addWidget(self._create_spacer(), 2, 0)

        # Row 2, Col 1: Bottom toolbar with border-top
        self.bottom_toolbar_container, bottom_toolbar_layout = self._create_toolbar(border_position="top", height=Theme.handleHeightBottom)

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
        self.btn_settings = CozyButton("Settings")
        self.btn_settings.clicked.connect(self.open_settings_window)
        bottom_toolbar_layout.addWidget(self.btn_settings)

        # Demo button
        self.btn_demo = CozyButton("Demo")
        self.btn_demo.clicked.connect(self.open_demo_window)
        bottom_toolbar_layout.addWidget(self.btn_demo)

        # Wait button (minimize - left of exit)
        self.btn_wait = CozyButton("Wait")
        self.btn_wait.clicked.connect(self.minimize_with_animation)
        bottom_toolbar_layout.addWidget(self.btn_wait)

        # Exit button (right-aligned)
        # Note: "Exid" is intentional stylization, not a typo - it's an exit button named exid
        self.btn_exit = CozyButton("Exid")
        # self.btn_exit.clicked.connect(lambda: (self.save_session(), self.close()))
        self.btn_exit.clicked.connect(lambda: self.safe_exit())
        bottom_toolbar_layout.addWidget(self.btn_exit)

        grid_layout.addWidget(self.bottom_toolbar_container, 2, 1)

        # Row 2, Col 2: Bottom right spacer
        grid_layout.addWidget(self._create_spacer(), 2, 2)

        # Set row/column stretch to make canvas expandable
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnStretch(1, 1)

        self.show()

        # Auto-load the last session (AFTER scene is fully initialized)
        self.auto_load()

    def setup_project_selector(self):
        """The Project Selector Combo Box"""

        self.project_selector = QComboBox()
        self.project_selector.setObjectName("project_selector")

        # Apply theme-driven stylesheet
        self.project_selector.setMinimumWidth(Theme.comboboxMinWidth)
        self.project_selector.setStyleSheet(f"""
            QComboBox#project_selector {{
                background-color: {Theme.comboboxBg.name()};
                color: {Theme.comboboxText.name()};
                border: 1px solid {Theme.comboboxBorder.name()};
                border-radius: {Theme.comboboxBorderRadius}px;
                padding: {Theme.comboboxPadding};
                font-family: {Theme.comboboxFontFamily};
                font-size: {Theme.comboboxFontSize}pt;
                font-weight: {Theme.comboboxFontWeight};
            }}
            QComboBox#project_selector::drop-down {{
                border: none;
                width: {Theme.comboboxDropdownWidth}px;
            }}
            QComboBox#project_selector QAbstractItemView {{
                background-color: {Theme.comboboxBgOpen.name()};
                color: {Theme.comboboxText.name()};
                border: 1px solid {Theme.comboboxBorder.name()};
                selection-background-color: {Theme.accentSelected.name()};
                font-family: {Theme.comboboxFontFamily};
                font-size: {Theme.comboboxFontSize}pt;
            }}
        """)

        self.project_selector.currentIndexChanged.connect(self.on_session_changed)

        return self.project_selector

    def auto_load(self):
        """Auto-load the last session if available."""
        session_names = self.populate_sessions()
        last_session = Settings.get("session/last_loaded", "")
        
        if last_session and session_names and last_session in session_names:
            index = self.project_selector.findText(last_session)
            if index >= 0:
                # Set the identity before loading
                self._current_session = last_session
                self.project_selector.setCurrentIndex(index)
                
                # Explicit load if signal doesn't fire (e.g., index was already 0)
                if index == 0:
                    self.load_session(last_session)

    def load_session(self, session_name: str):
        filepath = SessionManager.get_session_filename(session_name)
        data = SessionManager.get_session_data(filepath)
        if not data:
            return
        
        if data:
            # 1. Clear and Rebuild nodes (Your existing logic)
            self.view.setUpdatesEnabled(False)
            try:
                self.scene.clear_nodes()
                self.scene.rebuild_from_session(data)

                # 103% CERTAINTY: Force the 'Camera Operator' to look at the truth
                self.view.viewport().setUpdatesEnabled(True)
                self.view.viewport().repaint() # Synchronous paint (The Sledgehammer)
                
                # 1. Retrieve the Focal Length
                viewport = data.get("viewport", {})
                self.view_pan_x = viewport.get("center_x", 0.0)
                self.view_pan_y = viewport.get("center_y", 0.0)
                self.view_zoom = viewport.get("scale", 1.0) # Default to 1:1

                # 2. Sync the View's internal ledger
                # This is vital so the next scroll wheel event starts from the right place
                self.view.current_zoom = self.view_zoom

                # 3. Apply the Transformation
                # We reset to identity first to avoid 'Stacking' zooms on top of each other
                self.view.resetTransform()
                self.view.scale(self.view_zoom, self.view_zoom)

                # 4. Center the Camera
                self.view.centerOn(self.view_pan_x, self.view_pan_y)
                
                # Reset the 'First Interact' guard so the next pan is high-precision
                self.view._first_interact_done = False
                
            finally:
                self.scene.set_dirty(False)
                self.view.setUpdatesEnabled(True)
                self.view.viewport().setUpdatesEnabled(True)
                self.view.viewport().update()

    def save_session(self, session_name: str):
        """Gathers characters and camera state; forces the warehouse to acknowledge spaces."""
        if not session_name:
            logger.warning("Save failed: No session name provided.")
            return

        # 1. Gather the data (The Absolute Truth)
        data = self.scene.get_session_data()
        data["viewport"] = {
            "center_x": float(self.view_pan_x),
            "center_y": float(self.view_pan_y),
            "scale": float(self.view_zoom) # The Focal Length
        }
        
        # 2. Update Memory
        Settings.set("session/last_loaded", session_name)
        self._current_session = session_name
        
        # 3. Archive to the warehouse
        filepath = SessionManager.get_session_filename(session_name)
        SessionManager.save_session(filepath, data)
        
        # 4. BALANCE THE LEDGER: Update the 'Reference Point'
        # This prevents the Safe Exit from thinking we still have unsaved moves.
        self._last_saved_viewport = (self.view_pan_x, self.view_pan_y, self.view_zoom)
        self.scene.set_dirty(False)
        
        logger.info(f"✅ Archived '{session_name}' at {self._last_saved_viewport}")

    def on_session_changed(self, index: int):
        """Handle combobox selection change with auto-save for the outgoing session."""
        if index < 0: return
        new_session_name = self.project_selector.currentText()
        
        # 1. ACCOUNTABILITY: Check if the OLD session needs saving before we overwrite it
        # We only do this if we actually had a previous session active
        if hasattr(self, "_current_session") and self._current_session and self._current_session != new_session_name:
            
            current_view = (self.view_pan_x, self.view_pan_y, self.view_zoom)
            last_view = getattr(self, "_last_saved_viewport", (0.0, 0.0, 1.0))
            
            if self.scene.is_dirty() or current_view != last_view:
                logger.info(f"🔄 Auto-saving outgoing session: '{self._current_session}'")
                self.save_session(self._current_session)

        # 2. Record the identity of the NEW session
        Settings.set("session/last_loaded", new_session_name)
        self._current_session = new_session_name
        
        # 3. Bring the new characters and camera onto the stage
        self.load_session(new_session_name)

    def populate_sessions(self):
        """Populate with session names from sessions/ directory"""
        # Block signals during population to avoid loading before scene is initialized
        self.project_selector.blockSignals(True)

        session_names = SessionManager.get_available_sessions()
        if session_names:
            self.project_selector.addItems(session_names)
        else:
            self.project_selector.addItem("No sessions found")
        
        self.project_selector.blockSignals(False)

        return session_names

    def update_blur_intensity(self, value):
       Theme.frostColor.setAlpha(value)

       # Map the blur (Sane range 0-30 for performance)
       blur_radius = (value / 255) * 30

       # Update the fog layer to what the user actually sees
       visible_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
       self.scene.fog_layer.setRect(visible_rect)

       self.blur_slider.setToolTip(f"Optimized Smudge: {int(blur_radius)}px")
       self.view.viewport().update()

    def create_new_node(self):
        view_center = self.view.mapToScene(self.view.viewport().width() // 2, self.view.viewport().height() // 2)
        self.scene.add_node(view_center.x(), view_center.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < self.handle_height_top:
            self._dragging_window = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Move window when dragging the top bar."""
        if self._dragging_window:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + (new_pos - self._drag_pos))
            self._drag_pos = new_pos
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Stop dragging on mouse release."""
        self._dragging_window = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Toggle maximize/restore on double-click of title bar."""
        if event.position().y() < self.handle_height_top:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def minimize_with_animation(self):
        """Minimize window with custom shrink + fade animation."""
        self._animator.minimize(self)

    def changeEvent(self, event):
        """Handle window state changes to animate restore."""
        if event.type() == QEvent.WindowStateChange:
            if not (self.windowState() & Qt.WindowMinimized) and self._animator.is_minimized:
                # Window is being restored from minimized state
                logger.info("Window restored, starting restore animation")
                self._animator.restore(self)
        super().changeEvent(event)

    def showEvent(self, event):
        """
        PURPOSE: Trigger the visual 'Entry' and schedule the coordinate sync.
        CLAIM: The window is now 'Mapped', but we must handle the first-run safety.
        """
        super().showEvent(event)
        
        # 1. CASTING CHECK: Only stop the animation if it actually exists (is not None)
        if hasattr(self, "anim") and self.anim is not None:
            self.anim.stop()
        
        # 2. START THE FADE
        if self.windowOpacity() < 1.0:
            self.anim = QPropertyAnimation(self, b"windowOpacity")
            self.anim.setDuration(600)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim.start()

        # 3. THE HANDSHAKE: Schedule the Granite Sync
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.establish_granite_center)

    def establish_granite_center(self):
        """
        PURPOSE: Match the Viewport's physical camera to the Ledger's coordinates.
        CLAIM: Geometry is now stable. centerOn() will finally be accurate.
        """
        # We move the 'Camera Operator' to look at the spot defined in our Ledger.
        # This kills the 'First Click Snap' by ensuring the View is already 
        # perfectly aligned before the user ever touches the mouse.
        self.view.centerOn(self.view_pan_x, self.view_pan_y)
        
        # Log it for accountability
        logger.debug(f"Handshake Successful: Camera synced to Ledger at ({self.view_pan_x}, {self.view_pan_y})")

    def safe_exit(self):
        """Ensures the camera and nodes are saved if either has moved."""
        # If _current_session is None or empty, fall back to Settings
        session_name = self._current_session or Settings.get("session/last_loaded", "latest_session")
        
        current_view = (self.view_pan_x, self.view_pan_y, self.view_zoom)
        last_view = getattr(self, "_last_saved_viewport", (0.0, 0.0, 1.0))
        
        camera_moved = current_view != last_view

        if self.scene.is_dirty() or camera_moved:
            logger.info(f"Exit: Changes detected in '{session_name}'. Saving...")
            self.save_session(session_name)
        else:
            logger.info("Exit: Ledger is balanced. No save required.")
        
        self.close()

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