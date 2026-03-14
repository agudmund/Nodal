import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QSlider, QLineEdit, QCheckBox,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QSettings
from utils.logger import setup_logger
from utils.settings import Settings
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
        
        # Consistent Lookdev Styling
        self.setStyleSheet("""
            QDialog { background-color: #121212; color: #e0e0e0; }
            QTabWidget::pane { border: 1px solid #333; background: #1a1a1a; top: -1px; }
            QTabBar::tab {
                background: #252525;
                color: #888;
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { background: #1a1a1a; color: #fff; border: 1px solid #333; border-bottom: none; }
            QGroupBox { color: #888; font-weight: bold; border: 1px solid #333; margin-top: 20px; padding-top: 20px; }
            QLabel { color: #bbb; }
            QPushButton#saveBtn { background-color: #2d5a27; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton#saveBtn:hover { background-color: #3e7a36; }
            QPushButton#cancelBtn { background-color: #333; color: #bbb; padding: 8px; border-radius: 4px; }
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