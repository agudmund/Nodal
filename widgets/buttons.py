#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - buttons.py custom button components
# Reusable, styled buttons with cozy defaults

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont


class CozyButton(QPushButton):
    """
    Warm little button with cozy defaults.
    Encapsulates styling and behavior for consistency across the app.
    """

    def __init__(self, text: str = "Click me", parent=None):
        super().__init__(text, parent)

        # Size defaults
        self.setMinimumWidth(100)
        self.setMinimumHeight(36)

        # Mark this widget so the global stylesheet can target it
        self.setProperty("cozy", True)

        # Font defaults (Lato 13pt)
        font = self.font()
        font.setFamily("Lato")
        font.setPointSize(13)
        self.setFont(font)
