#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - extraWindow.py settings utility window
-Additional cozy utility dialog surface for settings and quick actions for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStyle,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLayout,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon

from utils.settings import Settings
# from utils.trello_api import TrelloAPI
# from utils.helpers import Helpers

# from widgets.about_dialog import AboutDialog


class ExtraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("The cozy beautiful settings home")
        self.setFixedSize(520, 520)
        self.setMinimumSize(520, 520)
        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(22)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.project_root = ""
        # self.project_root = Helpers.get_project_root()

        qpush = """
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
                color: #e0f0e0;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #444444; }
            QPushButton:disabled { background-color: #2a2a2a; color: #666666; }
        """
        qpushinactive = """
                    QPushButton {
                        background-color: #2a2a2a;
                        border: 1px solid #4a3a2f;
                        border-radius: 6px;
                        color: #a08a7a;
                        padding: 4px 8px;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #333333; color: #e0e0e0; }
                """

        # ── Trello Credentials Section ────────────────────────────────
        trello_row = QHBoxLayout()
        trello_row.setSpacing(12)

        trello_title = QLabel("Trello Credentials")
        trello_title.setFont(QFont("Lato", 14, QFont.Bold))
        trello_row.addWidget(trello_title)

        trello_row.addStretch()

        self.trello_status = QLabel("Not tested yet")
        self.trello_status.setStyleSheet("color: #8a7a67; font-size: 13px;")
        self.trello_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.trello_status.setWordWrap(False)
        trello_row.addWidget(self.trello_status)

        trello_row.addSpacing(16)

        test_cluster = QHBoxLayout()
        test_cluster.setSpacing(0)

        self.test_btn = QPushButton("Test")
        self.test_btn.setFixedHeight(28)
        self.test_btn.setFixedWidth(50)
        self.test_btn.clicked.connect(self.test_trello_connection)

        self.test_btn.setStyleSheet( qpush )

        test_cluster.addWidget(self.test_btn)
        trello_row.addLayout(test_cluster)

        layout.addLayout(trello_row)
        self._add_separator(layout)

        # ── App Icon Section ──────────────────────────────────────────
        app_row = QHBoxLayout()
        app_row.setSpacing(12)

        app_title = QLabel("App Window Icon")
        app_title.setFont(QFont("Lato", 14, QFont.Bold))
        app_row.addWidget(app_title)

        app_row.addStretch()

        self.app_status = QLabel("No custom icon set")
        self.app_status.setStyleSheet("color: #8a7a67; font-size: 13px;")
        app_row.addWidget(self.app_status)

        app_row.addSpacing(16)

        app_cluster = QHBoxLayout()
        app_cluster.setSpacing(8)

        self.app_preview = QLabel()
        self.app_preview.setFixedSize(32, 32)
        self.app_preview.setAlignment(Qt.AlignCenter)
        app_cluster.addWidget(self.app_preview)

        choose_app = QPushButton("Choose")
        choose_app.setFixedHeight(28)
        choose_app.setFixedWidth(90)
        choose_app.clicked.connect(self.choose_app_icon)

        reset_app = QPushButton("Reset")
        reset_app.setFixedHeight(28)
        reset_app.setFixedWidth(70)
        reset_app.clicked.connect(lambda: self.reset_icon("icon_path", self.app_status, self.app_preview))

        for btn in (choose_app, reset_app):
            btn.setStyleSheet( qpush)
            if btn.text() == "Reset":
                btn.setStyleSheet( qpushinactive)

        app_cluster.addWidget(choose_app)
        app_cluster.addWidget(reset_app)

        app_row.addLayout(app_cluster)
        layout.addLayout(app_row)

        # ── Bullet Icon Section ───────────────────────────────────────
        bullet_row = QHBoxLayout()
        bullet_row.setSpacing(12)

        bullet_title = QLabel("Feature List Bullet Icon")
        bullet_title.setFont(QFont("Lato", 14, QFont.Bold))
        bullet_row.addWidget(bullet_title)

        bullet_row.addStretch()

        self.bullet_status = QLabel("Using default")
        self.bullet_status.setStyleSheet("color: #8a7a67; font-size: 13px;")
        bullet_row.addWidget(self.bullet_status)

        bullet_row.addSpacing(16)

        bullet_cluster = QHBoxLayout()
        bullet_cluster.setSpacing(8)

        self.bullet_preview = QLabel()
        self.bullet_preview.setFixedSize(32, 32)
        self.bullet_preview.setAlignment(Qt.AlignCenter)
        bullet_cluster.addWidget(self.bullet_preview)

        choose_bullet = QPushButton("Choose")
        choose_bullet.setFixedHeight(32)
        choose_bullet.setFixedWidth(90)
        choose_bullet.clicked.connect(self.choose_bullet_icon)

        reset_bullet = QPushButton("Reset")
        reset_bullet.setFixedHeight(28)
        reset_bullet.setFixedWidth(70)
        reset_bullet.clicked.connect(lambda: self.reset_icon("bullet_icon_path", self.bullet_status, self.bullet_preview))

        for btn in (choose_bullet, reset_bullet):
            btn.setStyleSheet(qpush)
            if btn.text() == "Reset":
                btn.setStyleSheet(qpushinactive)

        bullet_cluster.addWidget(choose_bullet)
        bullet_cluster.addWidget(reset_bullet)

        bullet_row.addLayout(bullet_cluster)
        layout.addLayout(bullet_row)

        # ── About Section (bottom cozy footer) ────────────────────────────────
        about_btn = QPushButton("About Cushions")
        about_btn.setFixedHeight(28)
        about_btn.setStyleSheet(qpush)
        about_btn.clicked.connect(self.show_about)
        layout.addWidget(about_btn, alignment=Qt.AlignRight)

        layout.addStretch()
        self._refresh_statuses()

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(line)

    def _get_absolute_path(self, rel_or_abs_path: str | None) -> Path:
        if not rel_or_abs_path:
            return Path()
        p = Path(rel_or_abs_path)
        if p.is_absolute():
            return p.resolve()
        return (self.project_root / p).resolve()

    def _update_icon_status(self, key: str, status_label: QLabel, preview: QLabel, default_name: str, default_filename: str):
        stored_path = Settings.get(key)
        if stored_path:
            abs_path = self._get_absolute_path(stored_path)
            if abs_path.exists():
                status_label.setText(abs_path.name)
                pix = QPixmap(str(abs_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview.setPixmap(pix)
                return
        # Default fallback
        status_label.setText(default_name)
        default_path = ""
        # default_path = self.project_root / default_filename
        # if default_path.exists():
        #     pix = QPixmap(str(default_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #     preview.setPixmap(pix)
        # else:
        #     preview.setText("🖼️")  # tiny cozy placeholder

    def _refresh_statuses(self):
        self._update_icon_status("icon_path", self.app_status, self.app_preview,
                                 "Using default (icon.png)", "icon.png")
        self._update_icon_status("bullet_icon_path", self.bullet_status, self.bullet_preview,
                                 "Using default (bullet.png)", "bullet.png")

        # api_key, token = Settings.get_trello_creds()
        # if api_key and token:
        #     self.trello_status.setText("Credentials saved • Ready to test")
        # else:
        #     self.trello_status.setText("No credentials set yet")

    def choose_app_icon(self):
        start_dir = Settings.get_directory("last_dir_icon") or str(self.project_root)
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Select App Icon", start_dir, "Icons (*.ico *.png *.jpg *.jpeg)"
        )
        if not path_str:
            return
        chosen = Path(path_str)
        if not chosen.exists():
            return
        try:
            rel = chosen.relative_to(self.project_root).as_posix()
            self.parent().setWindowIcon(QIcon(str(chosen)))
            Settings.set("icon_path", rel)
            Settings.set_directory("last_dir_icon", str(chosen.parent))
            self._refresh_statuses()
            QMessageBox.information(self, "Success ✨", "App icon updated 🛋️")
        except ValueError:
            abs_str = str(chosen.resolve())
            Settings.set("icon_path", abs_str)
            Settings.set_directory("last_dir_icon", str(chosen.parent))
            self._refresh_statuses()
            QMessageBox.information(self, "Success ✨", "App icon updated (absolute path stored) 🛋️")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not set icon:\n{str(e)}")

    def choose_bullet_icon(self):
        start_dir = (
            Settings.get_directory("last_dir_bullet")
            or Settings.get_directory("last_dir_icon")
            or str(self.project_root)
        )
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Bullet Icon", start_dir, "Images (*.png *.ico *.jpg *.jpeg)"
        )
        if not path_str:
            return
        chosen = Path(path_str)
        if not chosen.exists():
            return
        try:
            rel = chosen.relative_to(self.project_root).as_posix()
            Settings.set("bullet_icon_path", rel)
            Settings.set_directory("last_dir_bullet", str(chosen.parent))
            self._refresh_statuses()
            QMessageBox.information(self, "Success ✨", "Bullet icon updated!\n(Re-open Feature List to see changes)")
        except ValueError:
            abs_str = str(chosen.resolve())
            Settings.set("bullet_icon_path", abs_str)
            Settings.set_directory("last_dir_bullet", str(chosen.parent))
            self._refresh_statuses()
            QMessageBox.information(self, "Success ✨", "Bullet icon updated (absolute path stored)!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not set bullet icon:\n{str(e)}")

    def reset_icon(self, key: str, status_label: QLabel, preview: QLabel):
        Settings.set(key, None)
        if key == "icon_path" and self.parent() and hasattr(self.parent(), '_init_window_icon'):
            self.parent()._init_window_icon()
        self._refresh_statuses()

    def test_trello_connection(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing…")
        self.trello_status.setText("Verifying your keys…")
        self.trello_status.setStyleSheet("color: #8a7a67; font-size: 13px;")

        try:
            TrelloAPI.from_settings()
            QMessageBox.information(
                self, "Connection Successful ✨",
                "Trello credentials are valid and working!\n\nYou're all set to create cozy boards 🌱"
            )
            self.trello_status.setText("Connected and ready ✓")
            self.trello_status.setStyleSheet("color: #a0d0a0; font-size: 13px;")
        except ValueError as e:
            msg = str(e)
            if "missing" in msg.lower():
                title = "Credentials Missing"
            else:
                title = "Invalid Credentials"
            QMessageBox.warning(self, title, msg)
            self.trello_status.setText("Keys look off")
            self.trello_status.setStyleSheet("color: #e08080; font-size: 13px;")
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"Something went wrong:\n{str(e)}")
            self.trello_status.setText("Hmm… issue")
            self.trello_status.setStyleSheet("color: #e08080; font-size: 13px;")
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Test")

    def show_about(self):
        AboutDialog(self).exec()