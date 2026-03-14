#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - settings_dialog.py application configuration
-Tabbed settings dialog for managing application preferences and node behavior
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QCheckBox, QLineEdit, QSlider, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QSettings, Signal
from utils.logger import setup_logger
from utils.settings import Settings
from utils.theme import Theme
from widgets.cozy_dialog import CozyDialog
from widgets.log_viewer_dialog import LogViewerDialog
from widgets import CozyButton


class SettingsDialog(CozyDialog):
    settingsChanged = Signal() 

    def __init__(self, parent=None):
        self.logger = setup_logger()

        # Initialize QSettings (Company Name, App Name)
        self.storage = QSettings("SingleSharedBraincell", "Nodal")

        # Call parent init with title
        super().__init__(title="The Fancy Settings Window 🌱", parent=parent)

        # Load values from registry/file
        self._load_settings()

    def _setup_content(self):
        """Build the tabbed content area."""
        self.tabs = QTabWidget()

        self._create_general_tab()
        self._create_nodes_tab()
        self._create_logs_tab()

        return self.tabs

    def _setup_bottom_buttons(self, layout):
        """Add Save and Cancel (Exid) buttons to the bottom bar.

        Note: "Exid" is our intentional stylization for the cancel/exit button,
        not a typo - it's part of the cozy aesthetic.
        """
        self.cancel_btn = CozyButton("Exid")
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_btn = CozyButton("Save")
        self.apply_btn.clicked.connect(self._apply_and_close)

        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.apply_btn)

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
