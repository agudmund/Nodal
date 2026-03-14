#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - cozy_dialog.py frameless utility dialog base
-Reusable base class for frameless dialogs with borders, draggable bars, and theme consistency
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget,
    QLabel
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from utils.theme import Theme


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
            QDialog {{ background-color: {window_bg}; color: {text_color}; }}
            QTabWidget::pane {{ background: {window_bg}; }}
            QTabBar::tab {{
                background: {Theme.COMBOBOX_BG.name()};
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
        titlebar_container.setFixedHeight(Theme.DIALOG_TOP_BAR_HEIGHT)
        titlebar_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-top: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            border-left: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            border-right: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
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
        if content_widget:
            main_layout.addWidget(content_widget, 1, 1)

        # Row 1, Col 2: Right spacer
        main_layout.addWidget(self._create_spacer("right"), 1, 2)

        # --- ROW 2: BOTTOM BAR ---
        # Row 2, Col 0: Bottom left corner spacer
        main_layout.addWidget(self._create_spacer("bottom-left"), 2, 0)

        # Row 2, Col 1: Bottom bar with buttons
        bottom_container = QWidget()
        bottom_container.setFixedHeight(Theme.DIALOG_BOTTOM_BAR_HEIGHT)
        bottom_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-bottom: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            border-left: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
            border-right: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};
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

        # Fade-in animation
        self._fadein()

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
            border_style = f"border-top: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()}; border-left: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"
        elif position == "top-right":
            border_style = f"border-top: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()}; border-right: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"
        elif position == "bottom-left":
            border_style = f"border-bottom: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()}; border-left: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"
        elif position == "bottom-right":
            border_style = f"border-bottom: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()}; border-right: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"
        elif position == "left":
            border_style = f"border-left: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"
        elif position == "right":
            border_style = f"border-right: {Theme.WINDOW_BORDER_WIDTH}px solid {Theme.TOOLBAR_BORDER.name()};"

        spacer.setStyleSheet(f"background-color: {Theme.WINDOW_BG.name()}; {border_style}")
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

    def mousePressEvent(self, event):
        """Handle window dragging from the top bar."""
        if event.button() == Qt.LeftButton and event.position().y() < Theme.DIALOG_TOP_BAR_HEIGHT:
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
