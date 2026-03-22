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

    def disconnect_all(self):
        """
        Sever all Qt signal connections and stop the animation.

        Called by BaseNode._prepare_for_removal before the node leaves its scene.
        Qt's C++ side holds its own references to signal connection targets —
        these are invisible to Python's GC. Without explicit disconnection,
        the valueChanged → node.setScale and finished → _reverse_pulse connections
        keep both the node wrapper and this NodeBehaviour alive indefinitely,
        preventing collection even after the node is removed from the scene.

        RuntimeError is caught and ignored on each disconnect — PySide6 raises it
        if a signal is already disconnected, which can happen during a fast purge
        or if the animation was never started.

        Do NOT call this from __del__ or any destructor path — by that point the
        C++ object may already be invalid and the disconnect call will segfault.
        Call it only while the node is still in the scene and all Qt APIs are valid.
        """
        try:
            self.pulse_anim.valueChanged.disconnect(self._node.setScale)
        except RuntimeError:
            pass
        try:
            self.pulse_anim.finished.disconnect(self._reverse_pulse)
        except RuntimeError:
            pass
        self.pulse_anim.stop()