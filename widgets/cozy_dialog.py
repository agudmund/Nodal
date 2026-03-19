#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - cozy_dialog.py frameless utility dialog base
-Reusable base class for frameless dialogs with borders and draggable bars for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget,
    QLabel
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter
from graphics.Theme import Theme


class WindowResizeHandle(QWidget):
    """
    Floating bottom-right resize grip for frameless windows.
    Mirrors BaseNode._draw_corner_taper — same PNG asset, same drag mechanic.
    Drop into any frameless QDialog or QMainWindow for consistent resize behaviour.
    """
    HANDLE_SIZE = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.HANDLE_SIZE, self.HANDLE_SIZE)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._drag_start_geom = QRect()

    def paintEvent(self, event):
        pixmap = Theme.getResizeGripPixmap()
        if pixmap and not pixmap.isNull():
            painter = QPainter(self)
            painter.drawPixmap(
                self.width()  - pixmap.width(),
                self.height() - pixmap.height(),
                pixmap
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_start_geom = self.window().geometry()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            geom  = self._drag_start_geom
            new_w = max(self.window().minimumWidth(),  geom.width()  + delta.x())
            new_h = max(self.window().minimumHeight(), geom.height() + delta.y())
            self.window().setGeometry(geom.x(), geom.y(), new_w, new_h)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()


class CozyDialog(QDialog):
    """
    Base class for utility dialogs with frameless design, draggable top bar,
    and consistent theme-driven styling. Subclasses only need to define content.
    """

    def __init__(self, title: str = "Dialog", parent=None):
        super().__init__(parent)

        # Dragging state for frameless window
        self._dragging_window = False
        self._drag_pos = None
        self._side_padding = 15

        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        self.resize(600, 650)

        # Frameless window to match main window design motif
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

         # Build stylesheet from Theme
        window_bg = Theme.windowBg.name()
        text_color = Theme.textPrimary.name()
        accent_color = Theme.accentNormal.name()
        accent_selected = Theme.accentSelected.name()

        # Consistent Lookdev Styling using Theme constants
        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {text_color}; }}
            QTabWidget::pane {{ background: {window_bg}; }}
            QTabBar::tab {{
                background: {Theme.comboboxBg.name()};
                color: {text_color};
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{ background: {window_bg}; color: {accent_selected}; }}
            QGroupBox {{ color: {text_color}; font-weight: bold; border: 1px solid {accent_color}; margin-top: 20px; padding-top: 20px; }}
            QLabel {{ color: {text_color}; }}
        """)

        # Main grid layout structure (3x3 grid)
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- ROW 0: TOP BAR ---
        # Row 0, Col 0: Top left corner spacer
        main_layout.addWidget(self._create_spacer("top-left"), 0, 0)

         # Row 0, Col 1: Top draggable bar
        titlebar_container = QWidget()
        titlebar_container.setFixedHeight(Theme.dialogTopBarHeight)
        titlebar_container.setStyleSheet(f"""
            background-color: {Theme.toolbarBg.name()};
            border-top: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};
        """)

        titlebar_layout = QHBoxLayout(titlebar_container)
        titlebar_layout.setContentsMargins(15, 0, 15, 0)
        titlebar_layout.addStretch()

        titlebar_label = QLabel(title)
        titlebar_label.setStyleSheet(f"color: {text_color}; font-weight: bold;")
        titlebar_layout.addWidget(titlebar_label)
        titlebar_layout.addStretch()

        main_layout.addWidget(titlebar_container, 0, 1)

        # Row 0, Col 2: Top right corner spacer
        main_layout.addWidget(self._create_spacer("top-right"), 0, 2)

        # --- ROW 1: CONTENT AREA ---
        # Row 1, Col 0: Left spacer
        main_layout.addWidget(self._create_spacer("left"), 1, 0)

        # Row 1, Col 1: Content (subclasses override this)
        content_widget = self._setup_content()
        self._content_widget = content_widget
        if content_widget:
            main_layout.addWidget(content_widget, 1, 1)

        # Row 1, Col 2: Right spacer
        main_layout.addWidget(self._create_spacer("right"), 1, 2)

        # --- ROW 2: BOTTOM BAR ---
        # Row 2, Col 0: Bottom left corner spacer
        main_layout.addWidget(self._create_spacer("bottom-left"), 2, 0)

         # Row 2, Col 1: Bottom bar with buttons
        bottom_container = QWidget()
        self._bottom_container = bottom_container
        bottom_container.setFixedHeight(Theme.dialogBottomBarHeight)
        bottom_container.setStyleSheet(f"""
            background-color: {Theme.toolbarBg.name()};
            border-bottom: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};
        """)

        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(15, 0, 15, 0)
        bottom_layout.addStretch()

        # Subclasses populate this layout
        self._setup_bottom_buttons(bottom_layout)

        main_layout.addWidget(bottom_container, 2, 1)

        # Row 2, Col 2: Bottom right corner spacer
        main_layout.addWidget(self._create_spacer("bottom-right"), 2, 2)

        # Set row/column stretch
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(1, 1)

        # Curtains + fade-in setup
        self._setup_curtains()

        # Fade-in animation
        self._fadein()

        # Resize grip — consistent with node resize handles
        self._resize_handle = WindowResizeHandle(self)
        self._reposition_resize_handle()
        self._resize_handle.show()

    def _create_spacer(self, position="middle"):
        """
        Create a standard padding spacer widget with selective borders.

        Args:
            position: "top-left", "top-right", "bottom-left", "bottom-right", "left", "right"
        """
        spacer = QWidget()
        spacer.setFixedWidth(self._side_padding)

        # Build border based on position
        border_style = ""
        if position == "top-left":
            border_style = f"border-top: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()}; border-left: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"
        elif position == "top-right":
            border_style = f"border-top: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()}; border-right: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"
        elif position == "bottom-left":
            border_style = f"border-bottom: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()}; border-left: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"
        elif position == "bottom-right":
            border_style = f"border-bottom: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()}; border-right: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"
        elif position == "left":
            border_style = f"border-left: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"
        elif position == "right":
            border_style = f"border-right: {Theme.windowBorderWidth}px solid {Theme.toolbarBorder.name()};"

        spacer.setStyleSheet(f"background-color: {Theme.windowBg.name()}; {border_style}")
        return spacer

    def _setup_content(self):
        """
        Override this to return the main content widget.
        Returns None if not overridden.
        """
        return None

    def _setup_bottom_buttons(self, layout):
        """
        Override this to add buttons to the bottom bar layout.
        The layout is already set up with stretch on the left.
        """
        pass

    def _fadein(self):
        """Animate the dialog fading in on show."""
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()

    # =========================================================================
    # Curtains — The Window Rollup Thing
    # =========================================================================

    def _setup_curtains(self):
        """Initialise curtains state and the multi-click patience timer."""
        self._click_count = 0
        self._click_patience = 350
        self._is_collapsed = False
        self._original_height = self.height()
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._execute_curtain_logic)

    def _increment_and_wait(self):
        """Count each press and restart the patience window."""
        self._click_timer.stop()
        self._click_count += 1
        self._click_timer.start(self._click_patience)

    def _execute_curtain_logic(self):
        """Run once clicking stops — double-click maximises, triple-click rolls up."""
        if self._click_count == 2:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        elif self._click_count >= 3:
            self.toggle_curtains()
        self._click_count = 0

    def toggle_curtains(self):
        """Animate the dialog into a sleek title-bar strip and back."""
        self.setMinimumHeight(0)
        self.curtain_anim = QPropertyAnimation(self, b"geometry")
        self.curtain_anim.setDuration(450)
        self.curtain_anim.setEasingCurve(QEasingCurve.OutExpo)

        start_rect = self.geometry()

        if not self._is_collapsed:
            self._original_height = self.height()
            end_rect = QRect(start_rect.x(), start_rect.y(), start_rect.width(), Theme.dialogTopBarHeight)
            if self._content_widget:
                self._content_widget.hide()
            if self._bottom_container:
                self._bottom_container.hide()
        else:
            end_rect = QRect(start_rect.x(), start_rect.y(), start_rect.width(), self._original_height)
            if self._content_widget:
                self._content_widget.show()
            if self._bottom_container:
                self._bottom_container.show()

        self.curtain_anim.setStartValue(start_rect)
        self.curtain_anim.setEndValue(end_rect)
        self.curtain_anim.start()

        self._is_collapsed = not self._is_collapsed

    def resizeEvent(self, event):
        """Keep the resize grip anchored to the bottom-right corner on every resize."""
        super().resizeEvent(event)
        if hasattr(self, '_resize_handle') and self._resize_handle:
            self._reposition_resize_handle()

    def _reposition_resize_handle(self):
        """Move the resize grip flush to the bottom-right corner and raise it above siblings."""
        h = self._resize_handle
        h.move(self.width() - h.width(), self.height() - h.height())
        h.raise_()

    def mousePressEvent(self, event):
        """Handle window dragging and curtain clicks from the top bar."""
        if event.button() == Qt.LeftButton and event.position().y() < Theme.dialogTopBarHeight:
            self._increment_and_wait()
            self._dragging_window = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Intercept OS double-click on the top bar so the click count stays accurate."""
        if event.position().y() < Theme.dialogTopBarHeight:
            self._increment_and_wait()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

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
