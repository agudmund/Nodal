#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - main_window.py main application window
-Frameless window with draggable toolbar and node graphics view for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QGridLayout, QWidget, QGraphicsView, QSlider, QComboBox, QGraphicsScene, QDialog, QInputDialog, QGraphicsTextItem, QCheckBox 
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QTransform, QIcon
from PySide6.QtCore import Qt, QEvent, QTimer, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup, QEasingCurve, QSize, QPoint, QRect, QDateTime
from graphics.Scene import NodeScene, enable_blur
from graphics.Theme import Theme
from widgets import CozyButton
from utils.logger import setup_logger, TRACE
from utils.settings import Settings
from utils.session_manager import SessionManager
from utils.window_animator import WindowAnimator
from widgets.settings_dialog import SettingsDialog
from widgets.demo_dialog import DemoDialog
from widgets.cozy_dialog import WindowResizeHandle
from widgets.extraWindow import ExtraDialog

logger = setup_logger()

# Windows ShowWindow flags for Aero animation
SW_MINIMIZE = 6
SW_RESTORE = 9

class NodeGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        # --- 1. The Foundation (Ledger & Anchors) ---
        self._first_interact_done = False
        self.viewport_locked = False
        self.setInteractive(True)
        
        # Stop Qt from trying to 'help' with placement
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setSceneRect(-5000, -5000, 10000, 10000)

        # --- 2. Disable The Frame (The Zero-Point Directive) ---
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.viewport().setContentsMargins(0, 0, 0, 0)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- 3. The Navigator (Internal State) ---
        self.current_zoom = 1.0
        self.zoom_speed = 0.002
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Consolidate: use underscore naming for internal mouse state
        self._last_pan_pos = None 
        self._last_zoom_pos = None
        self._alt_right_pressed = False

        # [DEBUG] Background paint call counter — throttles drawBackground diagnostic logging
        self._bg_paint_count = 0

        # --- 4. The Mica Core (Transparency & Quality) ---
        # Use a BspTree to make finding nodes faster in a large scene
        self.scene().setItemIndexMethod(QGraphicsScene.BspTreeIndex)

        self.viewport().setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # DontSavePainterState is intentionally omitted — with WA_TranslucentBackground and
        # QGraphicsDropShadowEffect on nodes, not saving painter state causes solid-color node
        # ghosts to bleed into the background layer via painter brush/transform leakage.
        try:
            self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustCursorShape)
        except AttributeError:
            pass
        self.setRenderHint(QPainter.Antialiasing)

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
        # [DEBUG] Logs the first 15 background paints — confirms draw order relative to item paints.
        # If background fires AFTER a node paint in the log, that explains the ghost bake-in.
        if self._bg_paint_count < 15:
            device_type = type(painter.device()).__name__
            t = painter.worldTransform()
            logger.log(
                TRACE,
                f"[BACKGROUND #{self._bg_paint_count}] device={device_type} "
                f"rect=({rect.x():.0f},{rect.y():.0f},{rect.width():.0f},{rect.height():.0f}) "
                f"viewport=({self.viewport().rect().width()},{self.viewport().rect().height()}) "
                f"scale=({t.m11():.3f},{t.m22():.3f})"
            )
            self._bg_paint_count += 1

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
            # We use position() for sub-pixel accuracy.
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
        if event.button() == Qt.MouseButton.MiddleButton:
            self._last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            # Explicitly clear any lingering grab state from the pan
            self.viewport().update()
            if self.scene() and self.scene().mouseGrabberItem():
                self.scene().mouseGrabberItem().ungrabMouse()
            event.accept()
            return

        if self._alt_right_pressed:
            self._alt_right_pressed = False
            self._last_zoom_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.active_editors = {} # Dictionary: {node_id: editor_instance}

        self._last_saved_viewport = (0.0, 0.0, 1.0)
        self.view_pan_x = 0.0
        self.view_pan_y = 0.0
        self.view_zoom = 1.0

        self.handle_height_top = Theme.handleHeightTop
        self._dragging_window = False
        self._drag_pos = None
        self._current_session = None        # Track current loaded session
        self._animator = WindowAnimator()   # Manages minimize/restore animations
        self._first_show = True             # Flag to trigger fade in on first show
        self.anim = None                    # Store fade in animation

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(500, 300)

        self.init_ui()
        enable_blur(int(self.winId()))

    def init_ui(self):
        self.setWindowTitle("Nodal")
        self.setGeometry(100, 100, 1200, 800)

        # Apply startup-only settings to Theme before anything is drawn
        Theme.debugNodeOverlay = Settings.is_debug_overlay_enabled()

        # Main central widget with grid layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.grid_layout = QGridLayout(central_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        self.setStyleSheet(f"""QMainWindow {{   background-color: {Theme.windowBg.name()};
                                                border: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};}}""")

        self._setupTopToolbar()     # The Collapsable Titlebar
        self._setupCentralGrid()    # Cental Grid Space Things
        self._setupBottomToolbar()  # Bottom Toolbar Things 
        self._setup_patience()      # Timers for the double click versus the triple click
        self.show()                 # Render The Actual Window Now That It Has Gone Through All These Steps Of Actually Getting Here
        self._resize_handle = WindowResizeHandle(self)
        self._reposition_resize_handle()
        self._resize_handle.show()
        self.auto_load()            # Auto-load the last session

    # =========================================================================
    # The Pile Of Mess It Takes To Build A Qt Window
    # The Mess, is Extraordinary, and has to be seen to be believed.
    # But if you don't have any particular reason to believe it, then dont go look.
    # =========================================================================
    def _setup_patience(self):
        """Timers for the double click versus the triple click"""
        self.click_count = 0
        self.click_patience = 350 # Default starting point
        self.is_collapsed = False
        self.was_maximized = False
        self.original_height = 800
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._execute_curtain_logic)

    def _setupTopToolbar(self):
        """The collapsable title bar"""
        self.grid_layout.addWidget(self._create_spacer(), 0, 0)

        self.toolbar_container, self.toolbar_layout = self._create_toolbar(border_position="bottom", height=Theme.handleHeightTop)

        self.toolbar_layout.addStretch()
        # add an icon file here right before the project selector to avoid the selection mechanism getting lost in translation
        self.toolbar_layout.addWidget(self.setup_project_selector())

        # INSERTED: The new icon button added right after the selector
        self.image_node_btn = self.setup_newCanvas_button(Theme.iconPathImage)
        self.toolbar_layout.addWidget(self.image_node_btn)
        self.toolbar_layout.addStretch()

        self.grid_layout.addWidget(self.toolbar_container, 0, 1)
        self.grid_layout.addWidget(self._create_spacer(), 0, 2)

    def setup_newCanvas_button(self, icon_path):
            """Creates a square, icon-only version of CozyButton"""
            
            # Pass empty string to avoid CozyButton's default text-padding logic
            btn = CozyButton("", self)
            
            # Set absolute square dimensions to match ComboBox height
            btn.setFixedSize(QSize(Theme.iconButtonSize, Theme.iconButtonSize))
            
            # Apply the icon
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(Theme.iconButtonSize - Theme.iconPadding, 
                                  Theme.iconButtonSize - Theme.iconPadding))
            
            # Override the horizontal padding of 15px from CozyButton.__init__
            btn.setStyleSheet(btn.styleSheet() + "QPushButton { padding: 0px; border-radius: 4px; }")
            
            # Connect to your future node logic
            btn.clicked.connect(self.newCanvas) 
            
            return btn

    def newCanvas(self):
        """Creates a brand new session file and switches to it."""
        from PySide6.QtWidgets import QInputDialog
        
        # 1. Get the name (Themed prompt or standard for now)
        name, ok = QInputDialog.getText(
            self, "✨ New Session", "Enter a name for your new canvas:",
            text=f"Session_{QDateTime.currentDateTime().toString('MMdd_HHmm')}"
        )

        if not ok or not name.strip():
            return

        session_name = name.strip()
        filepath = SessionManager.get_session_filename(session_name)

        # 2. CREATE THE FILE FIRST
        # This ensures that when load_session is called, the file actually exists
        if not Path(filepath).exists():
            initial_data = {"version": "1.0", "nodes": [], "connections": []}
            SessionManager.save_session(filepath, initial_data)
            logger.info(f"💾 Created new session file: {session_name}")

        # 1. Block signals so adding/setting doesn't fire multiple times
        self.project_selector.blockSignals(True)
        
        try:
            if self.project_selector.findText(session_name) == -1:
                self.project_selector.addItem(session_name)
            self.project_selector.setCurrentText(session_name)
        finally:
            self.project_selector.blockSignals(False)

        # 2. Manually trigger the load now that the UI is stable
        # self.on_session_changed(self.project_selector.currentIndex())
        # Stop recovery timer before the deferred session switch —
        # prevents contamination of the new empty session file during the 50ms window
        self.scene._recovery_timer.stop()
        
        self.view.clearFocus()
        self.scene.clearSelection()
        QTimer.singleShot(50, lambda: self.on_session_changed(self.project_selector.currentIndex()))

    def _setupCentralGrid(self):
        """The central area holding the actual nodal canvas"""
        self.grid_layout.addWidget(self._create_spacer(), 1, 0)

        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.view.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.view.setResizeAnchor(QGraphicsView.NoAnchor)

        # Initialize Ledger
        self.view_pan_x = 0.0
        self.view_pan_y = 0.0
        self.view_zoom = 1.0

        self.grid_layout.addWidget(self.view, 1, 1)

        # Row 1, Col 2: Right spacer
        self.grid_layout.addWidget(self._create_spacer(), 1, 2)

    def _setupBottomToolbar(self):
        """The lower toolbar with all the buttons"""

        # Row 2, Col 0: Bottom left spacer
        self.grid_layout.addWidget(self._create_spacer(), 2, 0)

        # Row 2, Col 1: Bottom toolbar with border-top
        self.bottom_toolbar_container, self.bottom_toolbar_layout = self._create_toolbar(border_position="top", height=Theme.handleHeightBottom)

        # New Node button (left-aligned)
        self.btn_new_node = CozyButton("Node")
        self.btn_new_node.clicked.connect(self.create_new_node)
        self.bottom_toolbar_layout.addWidget(self.btn_new_node)

        # Stretch to push exit button to the right
        self.bottom_toolbar_layout.addStretch()

        # The Blur Intensity Slider
        self.blur_slider = self._create_blur_slider()
        self.bottom_toolbar_layout.insertWidget(1, self.blur_slider)
        # Wiring mode toggle — shows/hides all ports globally
        self.chk_ports = QCheckBox("Wires")
        self.chk_ports.setChecked(False)
        self.chk_ports.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.comboboxText.name()};
                font-family: {Theme.comboboxFontFamily};
                font-size: {Theme.comboboxFontSize}pt;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {Theme.primaryBorder.name()};
                border-radius: 3px;
                background-color: {Theme.comboboxBg.name()};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.primaryBorder.name()};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.accentSelected.name()};
            }}
        """)
        self.chk_ports.stateChanged.connect(
            lambda state: self.scene.set_all_ports_visible(bool(state))
        )
        self.bottom_toolbar_layout.insertWidget(2, self.chk_ports)

        # Extra button
        self.btn_extra = CozyButton("Test")
        self.btn_extra.clicked.connect(self.open_extra_window)
        self.bottom_toolbar_layout.addWidget(self.btn_extra)

        # Settings button
        self.btn_settings = CozyButton("Settings")
        self.btn_settings.clicked.connect(self.open_settings_window)
        self.bottom_toolbar_layout.addWidget(self.btn_settings)

        # Exit button (right-aligned)
        # Note: "Exid" is intentional stylization, not a typo - it's an exit button named exid
        self.btn_exit = CozyButton("Exid")
        # self.btn_exit.clicked.connect(lambda: (self.save_session(), self.close()))
        self.btn_exit.clicked.connect(lambda: self.safe_exit())
        self.bottom_toolbar_layout.addWidget(self.btn_exit)

        self.grid_layout.addWidget(self.bottom_toolbar_container, 2, 1)

        # Row 2, Col 2: Bottom right spacer
        self.grid_layout.addWidget(self._create_spacer(), 2, 2)

        # Set row/column stretch to make canvas expandable
        self.grid_layout.setRowStretch(1, 1)
        self.grid_layout.setColumnStretch(1, 1)

    # =========================================================================
    # Utility Helpers
    # =========================================================================

    def open_settings_window(self):
        """Open the application settings dialog."""
        # We keep a reference so it doesn't get garbage collected
        self.settings_window = SettingsDialog(self)
        self.settings_window.show()

    def open_extra_window(self):
        """Open the application settings dialog."""
        # We keep a reference so it doesn't get garbage collected
        self.extra_window = ExtraDialog(self)
        self.extra_window.show()

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

        # Load saved blur opacity or fallback to theme default
        saved_blur_opacity = Settings.get_int("appearance/blur_opacity", Theme.frostColor.alpha())
        Theme.frostColor.setAlpha(saved_blur_opacity)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(saved_blur_opacity)
        slider.setFixedWidth(150)
        slider.setToolTip("Adjust Background Abstraction")

        # Build slider stylesheet with optional custom handle image
        handle_style = ""
        if Theme.sliderHandleImage:
            import os
            _resolved_slider_image = Theme._get_resource_path(Theme.sliderHandleImage)
            if os.path.exists(_resolved_slider_image):
                # Use custom image - convert path to URL format for stylesheet
                image_path = _resolved_slider_image.replace("\\", "/")
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
                logger.warning(f"Slider handle image not found: {_resolved_slider_image}, using solid color")
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
        # Save to settings on change
        slider.valueChanged.connect(lambda v: Settings.set("appearance/blur_opacity", v))
        return slider

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

    def _create_toolbar(self, border_position="bottom", height=None):
        """
        Create a toolbar container with consistent styling.

        Args:
            border_position: "top", "bottom", or None for no border
            height: Fixed height of the toolbar. Defaults to handleHeightTop if None.

        Returns:
            tuple: (container QWidget, layout QHBoxLayout)

        Note: This belongs in our reusable window util class as an app default applied to all windows
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

    # =========================================================================
    # Node And Session Stuff
    # =========================================================================

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

    def load_session(self, session_name: str, skip_clear: bool = False):

        filepath = SessionManager.get_session_filename(session_name)
        data = SessionManager.get_session_data(filepath)
        if not data:
            return

        if data:
            node_count = len(data.get("nodes", []))
            print ('node count %s' % node_count)
            conn_count = len(data.get("connections", []))
            logger.log(TRACE, f"[LOAD_SESSION] '{session_name}' — {node_count} nodes, {conn_count} connections")

            # 1. Clear and Rebuild nodes
            logger.log(TRACE, f"[LOAD_SESSION] setUpdatesEnabled(False)")
            self.view.setUpdatesEnabled(False)
            try:
                logger.log(TRACE, f"[LOAD_SESSION] clear_nodes()")
                if not skip_clear:                    # ← guard the inner one too
                    logger.log(TRACE, f"[LOAD_SESSION] clear_nodes()")
                    self.scene.clear_nodes()

                logger.log(TRACE, f"[LOAD_SESSION] rebuild_from_session()")
                self.scene.rebuild_from_session(data)
                logger.log(TRACE, f"[LOAD_SESSION] rebuild complete — resetting bg_paint_count for fresh diagnostics")
                self.view._bg_paint_count = 0

                # Retrieve the Focal Length
                viewport = data.get("viewport", {})
                self.view_pan_x = viewport.get("center_x", 0.0)
                self.view_pan_y = viewport.get("center_y", 0.0)
                self.view_zoom = viewport.get("scale", 1.0)
                logger.log(TRACE, f"[LOAD_SESSION] viewport — center=({self.view_pan_x:.1f},{self.view_pan_y:.1f}) zoom={self.view_zoom:.3f}")

                # Sync the View's internal ledger
                self.view.current_zoom = self.view_zoom

                # Apply the Transformation — reset to identity first to avoid stacking zooms
                self.view.resetTransform()
                # Clear mouse tracking state before transforming viewport
                # Prevents ungrab errors when the camera jumps from a previous session's position
                self.view.viewport().setMouseTracking(False)
                self.scene.clearSelection()
                if self.scene.mouseGrabberItem():
                    self.scene.mouseGrabberItem().ungrabMouse()
                self.view.viewport().setMouseTracking(True)

                # Apply the Transformation
                self.view.resetTransform()
                self.view.scale(self.view_zoom, self.view_zoom)
                self.view.centerOn(self.view_pan_x, self.view_pan_y)
                # Reset the 'First Interact' guard so the next pan is high-precision
                self.view._first_interact_done = False

            finally:
                self.scene.set_dirty(False)
                self.view.setUpdatesEnabled(True)
                self.view.viewport().setUpdatesEnabled(True)
                QTimer.singleShot(0, self.view.viewport().repaint)
                # Defer recovery timer restart — give the scene a full frame to settle
                # before arming the recovery writer. Prevents contamination of the new
                # session with stale scene state from the previous session's purge.
                QTimer.singleShot(500, self.scene._recovery_timer.start)

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

    def populate_sessions(self):
        """Populate with session names from sessions/ directory"""
        # Block signals during population to avoid loading before scene is initialized
        self.project_selector.blockSignals(True)

        session_names = [s for s in SessionManager.get_available_sessions() if s != "recovery"]
        if session_names:
            self.project_selector.addItems(session_names)
        else:
            self.project_selector.addItem("No sessions found")
        
        self.project_selector.blockSignals(False)

        return session_names

    def on_session_changed(self, index: int):
        if index < 0: return
        
        # Guard against recursive signals during setup
        if getattr(self, "_is_switching", False): return
        self._is_switching = True

        try:
            new_session_name = self.project_selector.currentText()
            
            # 1. Accountability: Save old session
            if hasattr(self, "_current_session") and self._current_session and self._current_session != new_session_name:
                self.save_session(self._current_session)

            # Pause recovery timer during session switch to prevent
            # contaminating the new session with outgoing session data
            self.scene._recovery_timer.stop()

            # 2. THE PURGE: Clear the stage and the registry
            self.scene.purge_session_items()
            self.scene.active_node_registry.clear()
            self.scene._undo_stack.clear()

            # 3. Identity
            self._current_session = new_session_name
            Settings.set("session/last_loaded", new_session_name)
            
            # 4. Rebuild (Now using the class-level registry)
            self.load_session(new_session_name, skip_clear=True)
            
        finally:
            self._is_switching = False

    def create_new_node(self):
        """Show the node type chooser popup centered over the canvas."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QPushButton
        from PySide6.QtGui import QColor

        chooser = QWidget(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        chooser.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        chooser.setFixedSize(760, 160)
        chooser.setObjectName("nodeTypeChooser")

        # Glow effect for extra coziness
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(24)
        glow.setColor(QColor(Theme.primaryBorder.red(), Theme.primaryBorder.green(), Theme.primaryBorder.blue(), 120))
        glow.setOffset(0, 0)
        chooser.setGraphicsEffect(glow)

        chooser.setStyleSheet(f"""
            QWidget#nodeTypeChooser {{
                background-color: {Theme.toolbarBg.name()};
                border: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};
                border-radius: 12px;
            }}
            QPushButton {{
                background-color: {Theme.comboboxBg.name()};
                color: {Theme.comboboxText.name()};
                border: 1px solid {Theme.comboboxBorder.name()};
                border-radius: 8px;
                padding: 10px 18px;
                font-family: {Theme.comboboxFontFamily};
                font-size: {Theme.comboboxFontSize}pt;
            }}
            QPushButton:hover {{
                background-color: {Theme.accentSelected.name()};
                border-color: {Theme.primaryBorder.name()};
            }}
            QLabel {{
                color: {Theme.comboboxText.name()};
                font-family: {Theme.comboboxFontFamily};
                font-size: {Theme.comboboxFontSize}pt;
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(chooser)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("What kind of node feels right today? ✨")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        def create_and_close(node_type: str):
            center = self.view.mapToScene(
                self.view.viewport().width() // 2,
                self.view.viewport().height() // 2
            )
            if node_type == "warm":
                self.scene.add_warm_node(center.x(), center.y())
            elif node_type == "bezier":
                self.scene.add_bezier_node(center.x(), center.y())
            elif node_type == "about":
                from graphics.AboutNode import AboutNode
                node = AboutNode(node_id=self.scene._next_node_id(), pos=center)
                self.scene._register_node(node)
            elif node_type == "image":
                from graphics.ImageNode import ImageNode
                node = ImageNode(node_id=self.scene._next_node_id(), pos=center)
                self.scene._register_node(node)
            elif node_type == "health":
                from graphics.HealthNode import HealthNode
                node = HealthNode(node_id=self.scene._next_node_id(), pos=center)
                self.scene._register_node(node)

            chooser.close()

        warm_btn = QPushButton("Warm 🌱")
        warm_btn.clicked.connect(lambda: create_and_close("warm"))
        btn_layout.addWidget(warm_btn)

        bezier_btn = QPushButton("Bezier 〜")
        bezier_btn.clicked.connect(lambda: create_and_close("bezier"))
        btn_layout.addWidget(bezier_btn)

        about_btn = QPushButton("About ❤️")
        about_btn.clicked.connect(lambda: create_and_close("about"))
        btn_layout.addWidget(about_btn)

        image_btn = QPushButton("Image 🖼️")
        image_btn.clicked.connect(lambda: create_and_close("image"))
        btn_layout.addWidget(image_btn)

        image_btn = QPushButton("Health 🩺")
        image_btn.clicked.connect(lambda: create_and_close("health"))
        btn_layout.addWidget(image_btn)

        layout.addLayout(btn_layout)

        # Center the popup over the canvas
        global_pos = self.view.mapToGlobal(
            self.view.viewport().rect().center()
        )
        chooser.move(global_pos - QPoint(chooser.width() // 2, chooser.height() // 2))
        chooser.show()
        chooser.raise_()

    # =========================================================================
    # The Glorious and Prestigious Mica
    # =========================================================================

    def update_blur_intensity(self, value):
        Theme.frostColor.setAlpha(value)
        # Map the blur (Sane range 0-30 for performance)
        blur_radius = (value / 255) * 30
        # Update the fog layer to what the user actually sees
        visible_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        self.scene.fog_layer.setRect(visible_rect)
        self.blur_slider.setToolTip(f"Optimized Smudge: {int(blur_radius)}px")
        self.view.viewport().update()

    # =========================================================================
    # Curtains, The Window Rollup Thing
    # Ported to CozyDialog — all floating dialogs now inherit this behaviour
    # =========================================================================

    def _increment_and_wait(self):
        """The Rolling Timer: Dials back the caffeine."""
        self.click_timer.stop()
        self.click_count += 1
        # Now, even at 400ms, it will feel responsive because we aren't losing clicks
        self.click_timer.start(self.click_patience)

    def _execute_curtain_logic(self):
        """The Decision Maker: Runs once the clicking stops."""
        # Use a small buffer; sometimes the OS sends extra events
        if self.click_count == 2:
            if self.isMaximized(): self.showNormal()
            else: self.showMaximized()
        elif self.click_count >= 3:
            self.toggle_curtains()
        
        self.click_count = 0

    def toggle_curtains(self):
        """Animate the window into a sleek HUD strip."""
        self.setMinimumHeight(0)
        self.curtain_anim = QPropertyAnimation(self, b"geometry")
        self.curtain_anim.setDuration(450)
        self.curtain_anim.setEasingCurve(QEasingCurve.OutExpo)

        start_rect = self.geometry()
        
        if not self.is_collapsed:
            # --- PULL CURTAINS ---
            self.original_height = self.height()
            # Collapse to exactly the draggable top-bar height
            end_rect = QRect(start_rect.x(), start_rect.y(), start_rect.width(), Theme.handleHeightTop)
            
            # Fade out the canvas to keep the HUD clean
            self.view.hide()
            if hasattr(self, 'bottom_toolbar_container'): self.bottom_toolbar_container.hide()
            logger.info(f"Curtains Pulled: Window height -> {Theme.handleHeightTop}px")
        else:
            # --- OPEN CURTAINS ---
            end_rect = QRect(start_rect.x(), start_rect.y(), start_rect.width(), self.original_height)
            self.view.show()
            if hasattr(self, 'bottom_toolbar_container'): self.bottom_toolbar_container.show()
            logger.info("Curtains Opened: Restoration complete.")

        self.curtain_anim.setStartValue(start_rect)
        self.curtain_anim.setEndValue(end_rect)
        self.curtain_anim.start()
        
        self.is_collapsed = not self.is_collapsed

    # =========================================================================
    # Things I haven't sorted and tidied up yet
    # =========================================================================

    def open_node_editor(self, node):
        """Launch or focus an editor for a specific node."""
        from graphics.NoteEditor import CozyNoteEditor
        
        # 1. CHECK THE REGISTRY: If this node is already being edited, just bring it to front
        if node.node_id in self.active_editors:
            existing_editor = self.active_editors[node.node_id]
            existing_editor.raise_()
            existing_editor.activateWindow()
            return

        # 2. CREATE NEW: Otherwise, manifest a new window
        editor = CozyNoteEditor(
            node_id=node.node_id,
            current_title=node.title,
            current_text=node.full_text,
            parent=self
        )
        
        # 3. REGISTER: Tie the editor to the node_id
        self.active_editors[node.node_id] = editor
        
        # 4. THE HANDSHAKE: Update node on Save, and Cleanup on Close
        editor.finished.connect(lambda result: self._handle_editor_finished(node, result))
        
        editor.show()

    def _handle_editor_finished(self, node, result):
        editor = self.active_editors.get(node.node_id)
        
        if result == QDialog.Accepted and editor:
            new_title = editor.get_title()
            new_text = editor.get_text()
            node.title = node._resolve_title(new_title, new_text)
            node.full_text = new_text
            node._last_full_text = None  # force body redraw
            node._sync_content_layout()
            node.update()
            self.scene.set_dirty(True)
            logger.info(f"💾 Parallel Sync: Node {node.node_id} updated.")

        if node.node_id in self.active_editors:
            del self.active_editors[node.node_id]

    def minimize_with_animation(self):
        """Minimize window with custom shrink + fade animation."""
        self._animator.minimize(self)

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

    # =========================================================================
    # Mouse and Hover Events
    # =========================================================================

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

    def keyPressEvent(self, event):
        """Route Backspace/Delete and Ctrl+Z to the scene.
        Guard: if a text item has keyboard focus (e.g. ImageNode caption edit),
        let the event reach it naturally — do not forward to the scene delete handler.
        """
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete) or \
           (event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier):
            # If a QGraphicsTextItem currently has focus, it owns this keystroke.
            # Forwarding to the scene would delete the node instead of editing text.
            scene = self.view.scene() if hasattr(self, 'view') else None
            if scene:
                if isinstance(scene.focusItem(), QGraphicsTextItem):
                    super().keyPressEvent(event)
                    return
                scene.keyPressEvent(event)
                return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """THE CURTAIN SENSOR: Every single press counts."""
        if event.button() == Qt.LeftButton and event.position().y() < Theme.handleHeightTop:
            self._increment_and_wait()
            
            # Keep dragging alive
            self._dragging_window = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """THE INTERCEPTOR: Catching the OS 'Double Click' event."""
        if event.position().y() < Theme.handleHeightTop:
            # Crucial: Increment here too, because the OS might skip the Press event!
            self._increment_and_wait()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        """
        PURPOSE: Provide stepped zooming via the mouse wheel.
        ACCOUNTABILITY: zoom_factor is relative. No cache update needed as the 
        ledger will be naturally captured during the next save.
        """
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.apply_zoom(zoom_factor)
        # The cache call is removed because the Ledger is the only truth now.

    # =========================================================================
    # App Core Events
    # =========================================================================

    def showEvent(self, event):
        """
        PURPOSE: Trigger the visual 'Entry' and schedule the coordinate sync.
        CLAIM: The window is now 'Mapped', but we must handle the first-run safety.
        """
        super().showEvent(event)
        
        # 1. CASTING CHECK: Only stop the animation if it actually exists (is not None)
        if hasattr(self, "anim") and self.anim is not None:
            self.anim.stop()
        
        # 2. Start The Fade
        if self.windowOpacity() < 1.0:
            self.anim = QPropertyAnimation(self, b"windowOpacity")
            self.anim.setDuration(600)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim.start()

        # 3. The Handsome Handshake: Schedule the Granite Sync
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.establish_granite_center)

    def changeEvent(self, event):
        """Handle window state changes to animate restore."""
        if event.type() == QEvent.WindowStateChange:
            if not (self.windowState() & Qt.WindowMinimized) and self._animator.is_minimized:
                # Window is being restored from minimized state
                logger.info("Window restored, starting restore animation")
                self._animator.restore(self)
        super().changeEvent(event)

    def resizeEvent(self, event):
        """Keep the resize handle anchored to the bottom-right corner on every resize."""
        super().resizeEvent(event)
        if hasattr(self, '_resize_handle') and self._resize_handle:
            self._reposition_resize_handle()

    def _reposition_resize_handle(self):
        """Move the resize grip flush to the bottom-right corner and raise it above all siblings."""
        h = self._resize_handle
        h.move(self.width() - h.width(), self.height() - h.height())
        h.raise_()

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