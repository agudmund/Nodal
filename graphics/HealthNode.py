#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - HealthNode.py live system health monitor
-A minimal diagnostic node that watches the garbage collector in real time for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import gc
import time
from PySide6.QtWidgets import QGraphicsTextItem
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QFont, QColor, QPen
from .BaseNode import BaseNode
from .Theme import Theme
from utils.logger import setup_logger, TRACE

logger = setup_logger()


class HealthNode(BaseNode):
    """
    A live system health monitor node.

    Polls the Python garbage collector on a configurable interval and displays
    the current node census directly on the canvas. Minimal footprint — AboutNode's
    clean shell with a live readout instead of static text.

    Does not serialize its readings — health state is always live, never restored
    from session. Restores as a fresh monitor on every load.

    Poll interval is tunable via POLL_INTERVAL_MS. The node marks itself
    non-dirty on poll so the health readout never triggers a session save.

    Click spy:
        Monkey-patches the scene's mousePressEvent on arrival to intercept
        and report what class and identity the top-most item under each click
        carries. Useful for identifying phantom or orphaned scene items that
        survive purge. The original handler is stored on self and fully restored
        on departure — no stacking, no leaking closures.

        Critical design rules:
        1. _original_scene_handler is always called unconditionally inside the spy —
           never inside a conditional block. Events must never be silently dropped.
        2. The spy closure captures health_ref (a local alias for self) not self
           directly. health_ref is used for all spy reads. self is only used
           at install/uninstall time when we know it is valid.
        3. _original_scene_handler is stored on self at install time and restored
           at uninstall time. This prevents spy stacking across session switches —
           each new HealthNode restores the scene to the genuine original before
           the next spy is installed.

    Silent error surface areas — all explicitly guarded and logged:
        - _poll_gc: gc.get_objects() RuntimeError during list mutation.
        - _poll_gc: scene() returning None mid-poll.
        - _poll_gc: scene.items() raising during heavy load.
        - _install_click_spy: scene None when deferred QTimer fires.
        - _install_click_spy: double-install guard via _spy_installed flag.
        - _click_spy: scene None at click time (node being removed).
        - _click_spy: original handler raising unexpectedly.
        - _uninstall_click_spy: scene None at departure.
        - itemChange: super() always called — skipping breaks Qt's item state machine.
        - paint_content: all fields initialised to safe defaults in __init__.
    """

    POLL_INTERVAL_MS = 2000       # How often to check the GC — gentle on performance
    DEFAULT_WIDTH    = 260.0
    DEFAULT_HEIGHT   = 230.0

    # Palette — warm amber for healthy, cooler tones for elevated counts
    COLOR_LABEL      = QColor("#a89a8a")   # Muted warm — secondary labels
    COLOR_VALUE_CALM = QColor("#8cbea0")   # Mint green — normal state (matches port output color)
    COLOR_VALUE_WARN = QColor("#d4a96a")   # Amber — elevated node count
    COLOR_VALUE_HIGH = QColor("#c97b7b")   # Rose — high node count, worth investigating
    WARN_THRESHOLD   = 50                  # Nodes in RAM before amber
    HIGH_THRESHOLD   = 150                 # Nodes in RAM before rose

    def __init__(self, node_id: int = 0, pos: QPointF = QPointF(0, 0),
                 width: float = DEFAULT_WIDTH, height: float = DEFAULT_HEIGHT,
                 uuid: str = None):
        """
        Initialize the HealthNode with zeroed live readings and start the poll timer.

        The first poll fires immediately after init so the node shows live data
        from the first frame rather than displaying zeroes until the first interval.
        Note: the first poll fires before the node is added to a scene, so
        _scene_nodes will correctly read 0 on that first call — this is expected.
        """
        logger.log(TRACE, f"[HEALTH] __init__ starting — node_id={node_id} pos=({pos.x():.1f},{pos.y():.1f})")

        super().__init__(
            node_id=node_id,
            title="Health",
            pos=pos,
            width=width,
            height=height,
            uuid=uuid
        )
        self.node_type = "health"
        self.setBrush(Theme.aboutNodeBg)

        # ── Live readings ──────────────────────────────────────────────────────
        # All fields initialised defensively — paint_content reads these before
        # the first poll completes, so None would cause a silent paint crash.
        self._living_nodes  = 0      # Total BaseNode instances Python's GC can see
        self._scene_nodes   = 0      # Nodes currently registered in the active scene
        self._last_gc_time  = 0.0    # Wall time (seconds) of the last GC census call
        self._poll_count    = 0      # Running count of successful polls since birth

        # ── Click spy readings ────────────────────────────────────────────────
        # Updated by _install_click_spy's scene monkey-patch on every mouse press.
        # Defaults to em dash so the paint rows always have something to display.
        self._last_clicked_type      = "—"    # Class name of top-most item under click
        self._last_clicked_item      = "—"    # Title or UUID fragment of that item
        self._spy_installed          = False   # Guard — prevents double-patching
        self._spy_install_timer      = None  # holds the pending QTimer so we can cancel it
        self._original_scene_handler = None   # Stored original — restored on departure

        # ── Poll timer ────────────────────────────────────────────────────────
        # Non-singleShot repeating timer — fires every POLL_INTERVAL_MS until
        # the node is removed from the scene. Stopped deterministically in
        # itemChange on scene departure rather than relying on GC timing.
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(self.POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_gc)
        self._poll_timer.start()
        logger.debug(f"[HEALTH] born — poll timer armed at {self.POLL_INTERVAL_MS}ms interval")

        # Run one immediate poll so the node shows live data from the first frame.
        # _scene_nodes will be 0 here since we're not in a scene yet — that's correct.
        self._poll_gc()

        logger.log(TRACE, f"[HEALTH] __init__ complete — uuid={self.uuid[:8]}")

    # ─────────────────────────────────────────────────────────────────────────
    # GC CENSUS
    # ─────────────────────────────────────────────────────────────────────────

    def _poll_gc(self):
        """
        Run a GC census and update all live readings.

        Collects generation 0 garbage before counting — gen 0 is fast and
        catches most short-lived cycles. Generations 1 and 2 are left to Python's
        automatic schedule to avoid stalling the paint loop.

        Scene node count is read from self.scene().items() separately from the
        GC count so we can compare live RAM objects against scene-visible objects.
        A persistent gap between the two indicates a reference leak.

        Marks the scene clean after update — health polling is observational.
        A poll is never a reason to trigger a session save or dirty the ledger.

        Every failure path is caught, logged at the appropriate severity level,
        and recovers gracefully. The poll count is always incremented so the
        footer confirms the node is alive even if a particular reading failed.
        """
        self._poll_count += 1
        logger.debug(f"[HEALTH] poll #{self._poll_count} starting")

        t0 = time.monotonic()

        try:
            # ── STEP 1: GC collect ────────────────────────────────────────────
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — calling gc.collect(0)")
            collected = gc.collect(0)
            logger.debug(f"[HEALTH] poll #{self._poll_count} — gc.collect(0) freed {collected} objects")

            # ── STEP 2: Count living BaseNode instances ───────────────────────
            # Import inside the method to avoid circular import at module load time.
            # BaseNode imports HealthNode via from_dict routing, so a top-level import
            # here would create a circular dependency.
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — importing BaseNode for isinstance check")
            from .BaseNode import BaseNode as _BaseNode

            try:
                logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — scanning gc.get_objects()")
                living_nodes = [obj for obj in gc.get_objects() if isinstance(obj, _BaseNode)]
                self._living_nodes = len(living_nodes)
                logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — found {self._living_nodes} living BaseNode instances")
            except RuntimeError as e:
                # gc.get_objects() can raise RuntimeError if the object list changes
                # during iteration — this is rare but real under heavy load.
                # Preserve the last known value rather than zeroing it out.
                logger.warning(
                    f"[HEALTH] poll #{self._poll_count} — gc.get_objects() raised RuntimeError: {e} "
                    f"— preserving last known living_nodes={self._living_nodes}"
                )

            # ── STEP 3: Count scene-visible nodes ─────────────────────────────
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — checking scene() for node count")
            if self.scene():
                try:
                    scene_items = self.scene().items()
                    self._scene_nodes = len([i for i in scene_items if isinstance(i, _BaseNode)])
                    logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — scene has {self._scene_nodes} BaseNode items")
                except Exception as e:
                    logger.warning(
                        f"[HEALTH] poll #{self._poll_count} — scene.items() raised {type(e).__name__}: {e} "
                        f"— scene_nodes defaulting to 0"
                    )
                    self._scene_nodes = 0
            else:
                self._scene_nodes = 0
                logger.debug(f"[HEALTH] poll #{self._poll_count} — not in scene, scene_nodes=0")

            self._last_gc_time = time.monotonic() - t0

            # ── STEP 4: Delta check ───────────────────────────────────────────
            delta = self._living_nodes - self._scene_nodes
            if delta > 0:
                logger.debug(
                    f"[HEALTH] poll #{self._poll_count} — "
                    f"living={self._living_nodes} scene={self._scene_nodes} "
                    f"delta=+{delta} ⚠ possible reference leak | "
                    f"last_click={self._last_clicked_type} / '{self._last_clicked_item}' | "
                    f"gc_time={self._last_gc_time * 1000:.1f}ms"
                )
            else:
                logger.debug(
                    f"[HEALTH] poll #{self._poll_count} — "
                    f"living={self._living_nodes} scene={self._scene_nodes} delta={delta} ✅ | "
                    f"gc_time={self._last_gc_time * 1000:.1f}ms"
                )

        except Exception as e:
            # Outer catch — something unexpected happened outside our specific guards.
            # Log loudly with full type info so it doesn't silently corrupt the readout.
            logger.error(
                f"[HEALTH] poll #{self._poll_count} — UNEXPECTED error in _poll_gc: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            self._last_gc_time = time.monotonic() - t0

        # ── STEP 5: Repaint ───────────────────────────────────────────────────
        logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — calling self.update()")
        self.update()

        # Do not mark dirty — health polling is observational, not a user change.
        if self.scene():
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — clearing dirty flag after update")
            self.scene().set_dirty(False)

        logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} complete")

    # ─────────────────────────────────────────────────────────────────────────
    # CLICK SPY
    # ─────────────────────────────────────────────────────────────────────────

    def _schedule_spy_install(self):
        """Cancel any pending install and schedule a fresh one."""
        if self._spy_install_timer is not None:
            self._spy_install_timer.stop()
            self._spy_install_timer = None
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self._install_click_spy)
        timer.start(250)  # 250ms — enough for load_session transforms to settle
        self._spy_install_timer = timer
        logger.log(TRACE, f"[HEALTH] spy install scheduled in 250ms")

    def _install_click_spy(self):
        """
        Monkey-patch the scene's mousePressEvent to intercept and report
        the top-most item under every mouse click.

        CRITICAL — original handler call rules:
            The original handler MUST be called unconditionally at the end of
            the spy, outside any if-block. Silent event dropping is the root
            cause of the previous recursion crash. If the spy swallows events,
            Qt's internal state machine gets confused and eventually explodes.

        CRITICAL — no spy stacking:
            _original_scene_handler is stored on self at install time.
            _uninstall_click_spy restores it on departure.
            If uninstall runs correctly, the next session's HealthNode installs
            its spy on top of the genuine original, not a previous spy.
            _spy_installed flag prevents double-install within one session.
        """
        logger.log(TRACE, f"[HEALTH] _install_click_spy called — scene={self.scene() is not None} spy_installed={self._spy_installed}")

        if not self.scene():
            logger.warning(
                f"[HEALTH] _install_click_spy — scene() is None. "
                f"Deferred QTimer fired after node was already removed from scene. Aborting."
            )
            return

        if self._spy_installed:
            logger.debug(f"[HEALTH] click spy already installed — skipping reinstall to prevent stacking")
            return

        # Store the genuine original before patching
        self._original_scene_handler = self.scene().mousePressEvent
        logger.log(TRACE, f"[HEALTH] original mousePressEvent stored: {type(self._original_scene_handler).__name__}")

        # Capture health_ref as a local — not self — to avoid the closure holding
        # a strong reference that would prevent GC collection of the HealthNode.
        health_ref = self
        original_ref = self._original_scene_handler  # local alias for the closure

        def _click_spy(event):
            """
            Intercept mouse press, read the top item, update HealthNode readings.

            The original handler is called UNCONDITIONALLY at the end.
            This is non-negotiable — event dropping causes Qt state machine corruption
            which manifests as silent recursion crashes that are impossible to trace.
            """
            logger.log(TRACE, f"[HEALTH SPY] mouse press intercepted at ({event.scenePos().x():.1f},{event.scenePos().y():.1f})")

            # Read-only inspection — never consume the event
            try:
                if health_ref.scene():
                    items_at_pos = health_ref.scene().items(event.scenePos())
                    logger.log(TRACE, f"[HEALTH SPY] {len(items_at_pos)} items at click position")
                    if items_at_pos:
                        top_item = items_at_pos[0]
                        health_ref._last_clicked_type = type(top_item).__name__
                        health_ref._last_clicked_item = (
                            getattr(top_item, 'title', None)
                            or getattr(top_item, 'uuid', None)
                            or str(id(top_item))[:8]
                        )
                        logger.debug(
                            f"[HEALTH] click detected — "
                            f"type={health_ref._last_clicked_type} "
                            f"identity='{health_ref._last_clicked_item}' "
                            f"pos=({event.scenePos().x():.1f},{event.scenePos().y():.1f})"
                        )
                    else:
                        health_ref._last_clicked_type = "— empty —"
                        health_ref._last_clicked_item = "—"
                        logger.debug(f"[HEALTH] click detected — no items at position")
                else:
                    logger.log(TRACE, f"[HEALTH SPY] scene() is None at click time — node being removed, skipping inspection")

            except Exception as e:
                logger.warning(
                    f"[HEALTH SPY] inspection raised {type(e).__name__}: {e} "
                    f"— original handler will still be called"
                )

            # ── UNCONDITIONAL original handler call ───────────────────────────
            # This line is outside every if/except block intentionally.
            # The original handler fires regardless of what happened above.
            # Commenting this out = silent event dropping = recursion crash.
            logger.log(TRACE, f"[HEALTH SPY] delegating to original handler")
            try:
                original_ref(event)
            except Exception as e:
                logger.error(
                    f"[HEALTH SPY] original handler raised {type(e).__name__}: {e}",
                    exc_info=True
                )

        self.scene().mousePressEvent = _click_spy
        self._spy_installed = True
        logger.debug(f"[HEALTH] click spy installed on scene — all mouse presses will be reported")

    def _uninstall_click_spy(self):
        """
        Restore the scene's original mousePressEvent.

        Called on scene departure to leave the scene completely clean.
        This prevents spy stacking — each new HealthNode installs its spy
        on the genuine original, not a previous spy's closure.

        If the scene is already None at uninstall time (race condition during
        rapid session switching), we log the situation and clear our flags anyway.
        The scene will be rebuilt from scratch on the next session load.
        """
        logger.log(TRACE, f"[HEALTH] _uninstall_click_spy called — spy_installed={self._spy_installed} scene={self.scene() is not None}")

        if not self._spy_installed:
            logger.log(TRACE, f"[HEALTH] click spy was not installed — nothing to uninstall")
            return

        if self.scene() and self._original_scene_handler is not None:
            self.scene().mousePressEvent = self._original_scene_handler
            logger.debug(f"[HEALTH] original mousePressEvent restored on scene — spy stack clean")
        else:
            logger.warning(
                f"[HEALTH] _uninstall_click_spy — could not restore original handler. "
                f"scene={self.scene() is not None} original_stored={self._original_scene_handler is not None}. "
                f"Scene will be rebuilt fresh on next session load regardless."
            )

        self._spy_installed = False
        self._original_scene_handler = None
        logger.log(TRACE, f"[HEALTH] click spy uninstall complete")

    # ─────────────────────────────────────────────────────────────────────────
    # PAINT
    # ─────────────────────────────────────────────────────────────────────────

    def paint_content(self, painter):
        """
        Render the live health readout inside the node body.

        Layout (top to bottom):
            ── header ── "🩺  Nodal Health"
            ── dotted divider ──
            Living nodes    [N]         — GC-visible BaseNode count, color-coded
            Scene nodes     [N]         — Scene-registered BaseNode count
            RAM delta       [+N / 0]    — Gap between living and scene, amber if > 0
            Last click      [ClassName] — Most recent clicked item type
              └ identity    [title/uuid]— Title or UUID of that item
            GC time         [N.Nms]     — Wall time of last census
            Poll #          [N]         — Total polls since birth
            ── dotted divider ──
            ── footer ── "polling every Ns  ·  spy active/inactive"

        All values read from instance state set by _poll_gc and _click_spy.
        No GC operations happen during paint — paint is read-only.
        """
        r      = self.rect()
        pad    = 12
        x      = pad
        y      = pad
        w      = r.width() - (pad * 2)
        line_h = 18

        label_font = QFont(Theme.nodeBodyFontFamily, 8)
        value_font = QFont(Theme.nodeBodyFontFamily, 9, QFont.Bold)
        head_font  = QFont(Theme.nodeTitleFontFamily, 10, QFont.Bold)
        tiny_font  = QFont(Theme.nodeBodyFontFamily, 7)

        # ── HEADER ────────────────────────────────────────────────────────────
        painter.setFont(head_font)
        painter.setPen(Theme.textPrimary)
        painter.drawText(int(x), int(y), int(w), line_h + 4,
                         Qt.AlignLeft | Qt.AlignVCenter, "🩺  Nodal Health")
        y += line_h + 6

        # ── DIVIDER ───────────────────────────────────────────────────────────
        divider_pen = QPen(Theme.primaryBorder, 1)
        divider_pen.setStyle(Qt.DotLine)
        painter.setPen(divider_pen)
        painter.drawLine(int(x), int(y), int(x + w), int(y))
        y += 8

        # ── ROWS ──────────────────────────────────────────────────────────────
        node_color = (
            self.COLOR_VALUE_HIGH if self._living_nodes >= self.HIGH_THRESHOLD else
            self.COLOR_VALUE_WARN if self._living_nodes >= self.WARN_THRESHOLD else
            self.COLOR_VALUE_CALM
        )

        delta = self._living_nodes - self._scene_nodes
        delta_color = self.COLOR_VALUE_WARN if delta > 0 else self.COLOR_VALUE_CALM
        delta_str   = f"+{delta}" if delta > 0 else str(delta)

        rows = [
            ("Living nodes",  str(self._living_nodes),           node_color),
            ("Scene nodes",   str(self._scene_nodes),            node_color),
            ("RAM delta",     delta_str,                          delta_color),
            ("Last click",    self._last_clicked_type,            Theme.textPrimary),
            ("  └ identity",  self._last_clicked_item,            self.COLOR_LABEL),
            ("GC time",       f"{self._last_gc_time * 1000:.1f}ms", Theme.textPrimary),
            ("Poll #",        str(self._poll_count),              self.COLOR_LABEL),
        ]

        for label, value, value_color in rows:
            painter.setFont(label_font)
            painter.setPen(self.COLOR_LABEL)
            painter.drawText(int(x), int(y), int(w * 0.6), line_h,
                             Qt.AlignLeft | Qt.AlignVCenter, label)
            painter.setFont(value_font)
            painter.setPen(value_color)
            painter.drawText(int(x), int(y), int(w), line_h,
                             Qt.AlignRight | Qt.AlignVCenter, value)
            y += line_h + 3

        # ── FOOTER DIVIDER ────────────────────────────────────────────────────
        y += 2
        painter.setPen(divider_pen)
        painter.drawLine(int(x), int(y), int(x + w), int(y))
        y += 6

        # ── FOOTER ───────────────────────────────────────────────────────────
        painter.setFont(tiny_font)
        painter.setPen(self.COLOR_LABEL)
        interval_s = self.POLL_INTERVAL_MS / 1000
        spy_status = "spy ✅" if self._spy_installed else "spy ⬜"
        painter.drawText(int(x), int(y), int(w), line_h,
                         Qt.AlignCenter,
                         f"every {interval_s:.0f}s  ·  {spy_status}")

    # ─────────────────────────────────────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────────────────────────────────────

    def itemChange(self, change, value):
        """
        Traffic director for HealthNode scene transitions.

        Arrival (ItemSceneChange, value is not None):
            Defers click spy installation by 100ms so the scene has fully
            settled before we patch its mousePressEvent. Installing immediately
            on arrival risks patching before the scene finishes its own setup.

        Departure (ItemSceneChange, value is None):
            Stops the poll timer immediately — there is no scene to read from
            and no canvas to paint to. Also uninstalls the click spy to restore
            the scene's original mousePressEvent cleanly.

        Always delegates to super() — BaseNode.itemChange handles _prepare_for_removal
        on departure. Skipping super() here would break the session independence
        contract established in BaseNode. This is not optional.
        """
        # Guard — itemChange can fire during super().__init__() before our
        # own __init__ has run. Check for our attributes before using them.
        if not hasattr(self, '_spy_installed'):
            return super().itemChange(change, value)

        logger.log(
            TRACE,
            f"[HEALTH] itemChange — change={change} value={'scene' if value is not None else 'None'} "
            f"spy={self._spy_installed} timer_active={self._poll_timer.isActive()}"
        )

        if change == self.GraphicsItemChange.ItemSceneChange:

            if self._spy_install_timer is not None:
                self._spy_install_timer.stop()
                self._spy_install_timer = None
                logger.log(TRACE, f"[HEALTH] cancelled pending spy install on departure")
            if value is not None:
                # Arriving in a scene — install click spy after scene settles
                logger.debug(f"[HEALTH] entering scene — scheduling click spy install in 100ms")
                self._schedule_spy_install()
            else:
                # Departing scene — stop timer and uninstall spy immediately
                logger.debug(
                    f"[HEALTH] leaving scene — stopping poll timer and uninstalling spy "
                    f"after {self._poll_count} polls"
                )
                self._poll_timer.stop()
                self._uninstall_click_spy()
                logger.debug(f"[HEALTH] departure cleanup complete")

        result = super().itemChange(change, value)
        logger.log(TRACE, f"[HEALTH] itemChange — super() returned, delegating result")
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # SERIALIZATION
    # ─────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Health state is always live — only structural identity is serialized.

        Readings (_living_nodes, _scene_nodes, _last_gc_time, click spy state)
        are deliberately excluded. The node restarts as a fresh monitor on every
        load, which is the correct behaviour — stale health readings from a
        previous session have no meaning in a new one.
        """
        data = super().to_dict()
        logger.log(TRACE, f"[HEALTH] to_dict — serializing structural identity only, uuid={self.uuid[:8]}")
        return data

    @staticmethod
    def from_dict(data: dict) -> 'HealthNode':
        """
        Deserialize a HealthNode from session data.

        Restores structural identity (position, size, port state) only.
        All live readings start fresh — see to_dict docstring for rationale.
        """
        logger.log(TRACE, f"[HEALTH] from_dict — restoring from session data node_id={data.get('node_id', 0)}")
        node = HealthNode(
            node_id=data.get("node_id", 0),
            pos=QPointF(data.get("pos_x", 0.0), data.get("pos_y", 0.0)),
            width=float(data.get("width",  HealthNode.DEFAULT_WIDTH)),
            height=float(data.get("height", HealthNode.DEFAULT_HEIGHT)),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        logger.debug(
            f"[HEALTH] restored from session — "
            f"node_id={node.node_id} uuid={node.uuid[:8]} "
            f"pos=({node.pos().x():.1f},{node.pos().y():.1f}) "
            f"size=({node.rect().width():.0f}x{node.rect().height():.0f})"
        )
        return node
