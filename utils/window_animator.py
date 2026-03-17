#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - window_animator.py frameless window animation
-Utility for smooth minimize/restore animations with frame-perfect rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtCore import QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QRect
from graphics.Theme import Theme
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

    @property
    def is_minimized(self) -> bool:
        """Check if window is currently in minimized state (has saved geometry to restore)."""
        return self._pre_minimize_geometry is not None

    def minimize(self, window):
        """
        Minimize window with custom shrink + fade animation.

        Args:
            window: The QMainWindow to animate

        Note on implementation: This uses manual intermediate keyframes rather than
        simple easing curves. This is intentional—when shrinking a large window to
        a small square, the per-frame pixel delta is massive. Without intermediate
        keyframes, the rendering pipeline struggles to keep up, causing visible
        stutter and frame drops. The manual keyframes provide granular interpolation
        steps that allow the GPU/display to render smoothly during the heavy shrink.

        Even with the architecture benefits of extracting this to a separate utility,
        the frame-perfect rendering requirement necessitates this approach. Simple
        easing curves cause noticeable jank during the aggressive geometry reduction.
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
        geom_anim = QPropertyAnimation(window, b"geometry")
        geom_anim.setDuration(Theme.windowAnimationDuration)
        geom_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Start from current geometry
        start_geom = window.geometry()

        # End at a small size in the bottom-right corner
        end_geom = QRect(
            start_geom.right() - 100,
            start_geom.bottom() - 100,
            50,
            50
        )

        # Add intermediate keyframes for smooth frame-perfect animation (9 total frames)
        # These are crucial for avoiding render stutter during the aggressive shrink
        geom_anim.setKeyValueAt(0.0, start_geom)
        geom_anim.setKeyValueAt(0.125, QRect(
            start_geom.x() + (start_geom.width() * 0.015),
            start_geom.y() + (start_geom.height() * 0.015),
            start_geom.width() * 0.97,
            start_geom.height() * 0.97
        ))
        geom_anim.setKeyValueAt(0.25, QRect(
            start_geom.x() + (start_geom.width() * 0.06),
            start_geom.y() + (start_geom.height() * 0.06),
            start_geom.width() * 0.88,
            start_geom.height() * 0.88
        ))
        geom_anim.setKeyValueAt(0.375, QRect(
            start_geom.right() - 175,
            start_geom.bottom() - 175,
            125,
            125
        ))
        geom_anim.setKeyValueAt(0.5, QRect(
            start_geom.right() - 150,
            start_geom.bottom() - 150,
            100,
            100
        ))
        geom_anim.setKeyValueAt(0.625, QRect(
            start_geom.right() - 137,
            start_geom.bottom() - 137,
            87,
            87
        ))
        geom_anim.setKeyValueAt(0.75, QRect(
            start_geom.right() - 125,
            start_geom.bottom() - 125,
            75,
            75
        ))
        geom_anim.setKeyValueAt(0.875, QRect(
            start_geom.right() - 112,
            start_geom.bottom() - 112,
            62,
            62
        ))
        geom_anim.setKeyValueAt(1.0, end_geom)

         # Animate opacity fade out
        # Opacity can use simple easing; it's not render-intensive like geometry
        opacity_anim = QPropertyAnimation(window, b"windowOpacity")
        opacity_anim.setDuration(Theme.windowAnimationDuration)
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
        geom_anim.setDuration(Theme.windowRestoreAnimationDuration)
        geom_anim.setStartValue(current_geom)
        geom_anim.setEndValue(target_geom)
        geom_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Animate opacity fade in
        opacity_anim = QPropertyAnimation(window, b"windowOpacity")
        opacity_anim.setDuration(Theme.windowRestoreAnimationDuration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self._restore_animation.addAnimation(geom_anim)
        self._restore_animation.addAnimation(opacity_anim)
        self._restore_animation.finished.connect(lambda: self._on_restore_finished(window))

        self._restore_animation.start()

    def _on_minimize_finished(self, window):
        """Called when minimize animation completes."""
        logger.info("Minimize animation finished, calling showMinimized()")
        window.showMinimized()
        self._animating = False

    def _on_restore_finished(self, window):
        """Called when restore animation completes. Syncs viewport position after restore."""
        # Re-establish the viewport position after animation completes
        # This ensures the canvas is in the exact same location as before minimize
        if hasattr(window, 'establish_granite_center'):
            window.establish_granite_center()
        self._animating = False
