#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - window_animator.py frameless window animation
-Utility for smooth minimize/restore animations with frame-perfect rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtCore import QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QRect
from utils.theme import Theme
from utils.logger import setup_logger

logger = setup_logger()


class WindowAnimator:
    """
    Manages smooth minimize/restore animations for frameless windows.

    Encapsulates animation state and logic to keep window management clean.
    """

    def __init__(self):
        """Initialize animation state."""
        self._animating = False
        self._minimize_animation = None
        self._restore_animation = None
        self._pre_minimize_geometry = None

    def minimize(self, window):
        """
        Minimize window with custom shrink + fade animation.

        Args:
            window: The QMainWindow to animate
        """
        if self._animating:
            return

        self._animating = True
        self._pre_minimize_geometry = window.geometry()

        logger.info("Starting custom minimize animation")

        # Stop any ongoing restore animation
        if self._restore_animation:
            self._restore_animation.stop()

        # Create parallel animation group (shrink + fade happen simultaneously)
        self._minimize_animation = QParallelAnimationGroup()

        # Animate geometry shrink (to bottom-right area, like taskbar)
        start_geom = window.geometry()
        end_geom = QRect(
            start_geom.right() - 100,
            start_geom.bottom() - 100,
            50,
            50
        )

        geom_anim = QPropertyAnimation(window, b"geometry")
        geom_anim.setDuration(Theme.WINDOW_ANIMATION_DURATION)
        geom_anim.setStartValue(start_geom)
        geom_anim.setEndValue(end_geom)
        geom_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Animate opacity fade out
        opacity_anim = QPropertyAnimation(window, b"windowOpacity")
        opacity_anim.setDuration(Theme.WINDOW_ANIMATION_DURATION)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self._minimize_animation.addAnimation(geom_anim)
        self._minimize_animation.addAnimation(opacity_anim)
        self._minimize_animation.finished.connect(lambda: self._on_minimize_finished(window))

        self._minimize_animation.start()

    def restore(self, window):
        """
        Animate window expanding and fading back in.

        Args:
            window: The QMainWindow to animate

        This uses clean easing curves instead of manual keyframes because
        expansion (small → large) has modest per-frame pixel deltas that the
        renderer handles smoothly. Compare to minimize() which needs manual
        keyframes to avoid stutter during aggressive shrinking.
        """
        if self._animating:
            return

        self._animating = True

        # Stop any ongoing minimize animation
        if self._minimize_animation:
            self._minimize_animation.stop()

        # Reset opacity to 0 before animating back in
        window.setWindowOpacity(0.0)

        logger.info("Starting custom restore animation")

        # Create parallel animation group (expand + fade in)
        self._restore_animation = QParallelAnimationGroup()

        # Animate geometry expand back to original
        current_geom = window.geometry()
        target_geom = self._pre_minimize_geometry

        geom_anim = QPropertyAnimation(window, b"geometry")
        geom_anim.setDuration(Theme.WINDOW_RESTORE_ANIMATION_DURATION)
        geom_anim.setStartValue(current_geom)
        geom_anim.setEndValue(target_geom)
        geom_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Animate opacity fade in
        opacity_anim = QPropertyAnimation(window, b"windowOpacity")
        opacity_anim.setDuration(Theme.WINDOW_RESTORE_ANIMATION_DURATION)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self._restore_animation.addAnimation(geom_anim)
        self._restore_animation.addAnimation(opacity_anim)
        self._restore_animation.finished.connect(self._on_restore_finished)

        self._restore_animation.start()

    def _on_minimize_finished(self, window):
        """Called when minimize animation completes."""
        logger.info("Minimize animation finished, calling showMinimized()")
        window.showMinimized()
        self._animating = False

    def _on_restore_finished(self):
        """Called when restore animation completes."""
        self._animating = False
