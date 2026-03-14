#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - settings_dialog.py application configuration for enjoying
-Tabbed settings dialog for managing application preferences and node behavior
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QSlider, QLineEdit, QCheckBox,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QSettings
from utils.logger import setup_logger
from utils.settings import Settings
from utils.theme import Theme
from widgets.log_viewer_dialog import LogViewerDialog


class SettingsDialog(QDialog):
    settingsChanged = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()

        # Initialize QSettings (Company Name, App Name)
        self.storage = QSettings("SingleSharedBraincell", "Nodal")

        self.setWindowTitle("Settings 🌱")
        self.setFixedSize(550, 600)

        # Frameless window to match main window design motif
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Build stylesheet from Theme
        window_bg = Theme.WINDOW_BG.name()
        text_color = Theme.TEXT_PRIMARY.name()
        accent_color = Theme.ACCENT_NORMAL.name()
        accent_selected = Theme.ACCENT_SELECTED.name()

        # Consistent Lookdev Styling using Theme constants
        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {text_color}; }}
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
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self._create_general_tab()
        self._create_nodes_tab()
        self._create_logs_tab() # Nested Viewer

        layout.addWidget(self.tabs)
        
        # 2. Bottom Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = QPushButton("Save Cozy Changes")
        self.apply_btn.setObjectName("saveBtn")
        self.apply_btn.clicked.connect(self._apply_and_close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        # Load values from registry/file
        self._load_settings()
        self._fadein()

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