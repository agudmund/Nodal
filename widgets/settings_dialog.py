#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - settings_dialog.py application configuration for enjoying
-Tabbed settings dialog for managing application preferences and node behavior
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QSlider, QLineEdit, QCheckBox,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QSettings, QPoint
from utils.logger import setup_logger
from utils.settings import Settings
from utils.theme import Theme
from widgets.log_viewer_dialog import LogViewerDialog


class SettingsDialog(QDialog):
    settingsChanged = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()

        # Dragging state for frameless window
        self._dragging_window = False
        self._drag_pos = None
        self._titlebar_height = Theme.HANDLE_HEIGHT
        self._side_padding = 15

        # Initialize QSettings (Company Name, App Name)
        self.storage = QSettings("SingleSharedBraincell", "Nodal")

        self.setWindowTitle("Settings 🌱")
        self.setFixedSize(600, 650)

        # Frameless window to match main window design motif
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        # Build stylesheet from Theme
        window_bg = Theme.WINDOW_BG.name()
        text_color = Theme.TEXT_PRIMARY.name()
        accent_color = Theme.ACCENT_NORMAL.name()
        accent_selected = Theme.ACCENT_SELECTED.name()

        # Consistent Lookdev Styling using Theme constants
        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {text_color}; border: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()}; }}
            QTabWidget::pane {{ border: 1px solid {accent_color}; background: {window_bg}; top: -1px; }}
            QTabBar::tab {{
                background: {Theme.COMBOBOX_BG.name()};
                color: {text_color};
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{ background: {window_bg}; color: {accent_selected}; border: 1px solid {accent_color}; border-bottom: none; }}
            QGroupBox {{ color: {text_color}; font-weight: bold; border: 1px solid {accent_color}; margin-top: 20px; padding-top: 20px; }}
            QLabel {{ color: {text_color}; }}
            QPushButton#saveBtn {{ background-color: {accent_color}; color: {window_bg}; font-weight: bold; padding: 8px; border-radius: 4px; }}
            QPushButton#saveBtn:hover {{ background-color: {accent_selected}; }}
            QPushButton#cancelBtn {{ background-color: {Theme.BUTTON_BG_INACTIVE.name()}; color: {text_color}; padding: 8px; border-radius: 4px; }}
        """)

        # Main grid layout structure (matching main_window pattern)
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Row 0, Col 0: Top left spacer
        main_layout.addWidget(self._create_spacer(), 0, 0)

        # Row 0, Col 1: Top draggable bar
        titlebar_container = QWidget()
        titlebar_container.setFixedHeight(self._titlebar_height)
        titlebar_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-bottom: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
        """)

        titlebar_layout = QHBoxLayout(titlebar_container)
        titlebar_layout.setContentsMargins(15, 0, 15, 0)
        titlebar_layout.addStretch()

        titlebar_label = QLabel("Settings 🌱")
        titlebar_label.setStyleSheet(f"color: {text_color}; font-weight: bold;")
        titlebar_layout.addWidget(titlebar_label)
        titlebar_layout.addStretch()

        main_layout.addWidget(titlebar_container, 0, 1)

        # Row 0, Col 2: Top right spacer
        main_layout.addWidget(self._create_spacer(), 0, 2)

        # Row 1, Col 0: Left spacer
        main_layout.addWidget(self._create_spacer(), 1, 0)

        # Row 1, Col 1: Tabs content area
        self.tabs = QTabWidget()

        self._create_general_tab()
        self._create_nodes_tab()
        self._create_logs_tab()

        main_layout.addWidget(self.tabs, 1, 1)

        # Row 1, Col 2: Right spacer
        main_layout.addWidget(self._create_spacer(), 1, 2)

        # Row 2, Col 0: Bottom left spacer
        main_layout.addWidget(self._create_spacer(), 2, 0)

        # Row 2, Col 1: Bottom bar with buttons
        bottom_container = QWidget()
        bottom_container.setFixedHeight(self._titlebar_height)
        bottom_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-top: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
        """)

        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(15, 0, 15, 0)
        bottom_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Save Cozy Changes")
        self.apply_btn.setObjectName("saveBtn")
        self.apply_btn.clicked.connect(self._apply_and_close)

        bottom_layout.addWidget(self.cancel_btn)
        bottom_layout.addWidget(self.apply_btn)

        main_layout.addWidget(bottom_container, 2, 1)

        # Row 2, Col 2: Bottom right spacer
        main_layout.addWidget(self._create_spacer(), 2, 2)

        # Set row/column stretch
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(1, 1)

        # Load values from registry/file
        self._load_settings()
        self._fadein()

    def _create_spacer(self):
        """Create a standard padding spacer widget."""
        spacer = QWidget()
        spacer.setFixedWidth(self._side_padding)
        spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()};")
        return spacer

    def _create_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        self.high_dpi_cb = QCheckBox("Enable High-DPI PassThrough")
        self.restore_geom_cb = QCheckBox("Remember window position")
        form.addRow(self.high_dpi_cb)
        form.addRow(self.restore_geom_cb)
        self.tabs.addTab(tab, "General")

    def _create_nodes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("Node Behavior")
        form = QFormLayout(group)
        
        self.default_label_edit = QLineEdit("Nodal 🌱")
        form.addRow("Default Label:", self.default_label_edit)
        
        self.blur_intensity = QSlider(Qt.Horizontal)
        self.blur_intensity.setRange(0, 100)
        self.blur_intensity.setValue(30)
        form.addRow("Background Blur:", self.blur_intensity)

        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Nodes")

    def _create_logs_tab(self):
        # Here we nest the actual LogViewerDialog
        # We pass 'self' as parent, but strip the window flags so it embeds
        self.log_viewer = LogViewerDialog(self)
        self.log_viewer.setWindowFlags(Qt.Widget) 
        # Optionally hide the viewer's own 'Refresh' buttons to avoid UI clutter
        self.tabs.addTab(self.log_viewer, "Logs")

    def _load_settings(self):
        """Pull values from our custom Settings wrapper on launch."""
        # We use the convenience methods we just built in settings.py
        self.high_dpi_cb.setChecked(Settings.is_high_dpi_enabled())
        
        # Or use the generic .get_bool() for specific keys
        self.restore_geom_cb.setChecked(Settings.get_bool("interface/restore_geom", True))
        
        # For the Node Label
        self.default_label_edit.setText(Settings.get_default_node_label())

    def _apply_and_close(self):
        """Save everything to the .ini file and close."""
        # 1. Save via the wrapper
        Settings.set_high_dpi(self.high_dpi_cb.isChecked())
        Settings.set("interface/restore_geom", self.restore_geom_cb.isChecked())
        Settings.set("nodes/default_label", self.default_label_edit.text().strip())
        
        # 2. Log the success (Settings.set already calls sync() internally)
        self.logger.info("Settings saved — cozy changes applied to nodal_config.ini 🌱")
        
        # 3. Notify the rest of the app and close
        self.settingsChanged.emit()
        self.accept()

    def _fadein(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()

    def mousePressEvent(self, event):
        """Handle window dragging from the top bar."""
        if event.button() == Qt.LeftButton and event.position().y() < self._titlebar_height:
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