#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - NodeBehaviour.py node ambient behaviour manager
-Handles node personality and ambient animations, keeping BaseNode focused on structure for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import random
from PySide6.QtCore import QVariantAnimation, QEasingCurve
from graphics.Theme import Theme
from utils.logger import setup_logger

logger = setup_logger()


class NodeBehaviour:
    """
    Manages ambient behaviour and personality for a node.
    Owns all animation state that isn't core to the node's structural function.

    Attach one instance per node in BaseNode.__init__:
        self.behaviour = NodeBehaviour(self)

    Currently handles:
        - Hover pulse animation (breathe in, breathe out)

    Designed as a container for future ambient behaviours:
        - Idle motion
        - Neighbour pathfinding
        - Attention seeking
        - Whatever the nodes decide they want to do
    """

    def __init__(self, node):
        """
        Initialize behaviour manager for a node.

        Args:
            node: The BaseNode instance this behaviour belongs to
        """
        self._node = node

        # Pulse animation — each node gets its own random duration at birth
        # so they never settle in unison, like blades of grass after a gust of wind
        self.pulse_anim = QVariantAnimation()
        pulse_duration = random.randint(Theme.nodePulseMin, Theme.nodePulseMax)
        self.pulse_anim.setDuration(pulse_duration)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(Theme.nodePulseScale)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pulse_anim.valueChanged.connect(self._node.setScale)

        # Wire reverse once at init — never reconnected on hover
        self.pulse_anim.finished.connect(self._reverse_pulse)

    def on_hover_enter(self):
        """Breathe in — start the pulse on hover enter."""
        if self.pulse_anim.state() == QVariantAnimation.Stopped:
            self.pulse_anim.setDirection(QVariantAnimation.Forward)
            self.pulse_anim.start()

    def on_hover_leave(self):
        """Breathe out — let the animation finish naturally, reverse handles the rest."""
        pass  # The reverse_pulse callback takes care of settling

    def _reverse_pulse(self):
        """Called when forward pulse completes — reverses back to resting scale."""
        if self.pulse_anim.direction() == QVariantAnimation.Forward:
            self.pulse_anim.setDirection(QVariantAnimation.Backward)
            self.pulse_anim.start()