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
from PySide6.QtCore import Qt, QPointF, QTimer, QObject, QEvent
from PySide6.QtGui import QFont, QColor, QPen
from .BaseNode import BaseNode
from .Theme import Theme
from utils.logger import setup_logger, TRACE

logger = setup_logger()


class _SceneClickFilter(QObject):
    """
    Qt event filter that intercepts mouse press events on the scene viewport
    to report what item was clicked, updating the HealthNode's diagnostic display.

    Replaces the previous monkey-patch approach entirely.

    Why an event filter instead of monkey-patching mousePressEvent:
        Monkey-patching requires storing and restoring function references,
        which creates a timing-dependent system — uninstall must happen before
        the next install, original references must be preserved across session
        switches, and any race between timer callbacks and session teardown
        causes silent C++ crashes. Qt's event filter system has none of these
        properties: installEventFilter and removeEventFilter are both
        deterministic and idempotent, no references are stored or restored,
        and calling removeEventFilter on a filter that was never installed
        (or was already removed) is a safe no-op.

    Design:
        - Installed on the viewport (view.viewport()), not the scene or view.
          The viewport receives raw input events before Qt's scene machinery
          translates them to scene coordinates.
        - Returns False unconditionally — never consumes events.
          This filter is read-only. The event always continues to its destination.
        - Holds a direct reference to the HealthNode for writing click readings.
          This is safe because the filter is owned by the HealthNode and removed
          before the HealthNode is destroyed.
    """

    def __init__(self, health_node: 'HealthNode'):
        super().__init__()
        self._health = health_node

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            try:
                scene = self._health.scene()
                if scene and scene.views():
                    view = scene.views()[0]
                    scene_pos = view.mapToScene(event.pos())
                    items_at_pos = scene.items(scene_pos)
                    if items_at_pos:
                        top_item = items_at_pos[0]
                        self._health._last_clicked_type = type(top_item).__name__
                        self._health._last_clicked_item = (
                            getattr(top_item, 'title', None)
                            or getattr(top_item, 'uuid', None)
                            or str(id(top_item))[:8]
                        )
                        logger.debug(
                            f"[HEALTH] click detected — "
                            f"type={self._health._last_clicked_type} "
                            f"identity='{self._health._last_clicked_item}' "
                            f"pos=({scene_pos.x():.1f},{scene_pos.y():.1f})"
                        )
                    else:
                        self._health._last_clicked_type = "— empty —"
                        self._health._last_clicked_item = "—"
                        logger.debug(f"[HEALTH] click detected — no items at position")
            except Exception as e:
                logger.warning(f"[HEALTH FILTER] eventFilter raised {type(e).__name__}: {e}")

        return False  # Never consume — always pass the event through


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

    Click detection:
        Uses a Qt event filter (_SceneClickFilter) installed on the scene's
        viewport to intercept mouse press events and report the top-most item
        under each click. Useful for identifying phantom or orphaned scene items
        that survive purge.

        The event filter is installed synchronously when the node enters the
        scene and removed synchronously when it leaves — no timers, no stored
        function references, no race conditions. installEventFilter and
        removeEventFilter are both deterministic and idempotent.

    Silent error surface areas — all explicitly guarded and logged:
        - _poll_gc: gc.get_objects() RuntimeError during list mutation.
        - _poll_gc: scene() returning None mid-poll.
        - _poll_gc: scene.items() raising during heavy load.
        - _SceneClickFilter.eventFilter: any exception during item inspection.
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

        # ── Click filter readings ─────────────────────────────────────────────
        # Updated by _SceneClickFilter.eventFilter on every mouse press.
        # Defaults to em dash so the paint rows always have something to display.
        self._last_clicked_type = "—"   # Class name of top-most item under click
        self._last_clicked_item = "—"   # Title or UUID fragment of that item
        self._click_filter      = None  # _SceneClickFilter instance — None when not installed

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

        Full collection across all three generations — deleted nodes are promoted
        to gen 1/2 quickly, so a gen-0-only sweep would leave them alive and
        inflate the living count after every delete.

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
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — calling gc.collect()")
            collected = gc.collect()
            logger.debug(f"[HEALTH] poll #{self._poll_count} — gc.collect() freed {collected} objects")

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
            logger.error(
                f"[HEALTH] poll #{self._poll_count} — UNEXPECTED error in _poll_gc: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            self._last_gc_time = time.monotonic() - t0

        # ── STEP 5: Repaint ───────────────────────────────────────────────────
        logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — calling self.update()")
        self.update()

        if self.scene():
            logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} — clearing dirty flag after update")
            self.scene().set_dirty(False)

        logger.log(TRACE, f"[HEALTH] poll #{self._poll_count} complete")

    # ─────────────────────────────────────────────────────────────────────────
    # CLICK FILTER
    # ─────────────────────────────────────────────────────────────────────────

    def _install_click_filter(self):
        """
        Install the event filter on the scene's viewport.

        Called synchronously on ItemSceneHasChanged (node fully entered scene)
        — no timer, no deferred callback. The viewport is valid at this point.
        Idempotent — safe to call if the filter is already installed.
        """
        if self._click_filter is not None:
            return
        if not self.scene() or not self.scene().views():
            logger.warning(f"[HEALTH] _install_click_filter — no scene or views, skipping")
            return
        self._click_filter = _SceneClickFilter(self)
        self.scene().views()[0].viewport().installEventFilter(self._click_filter)
        logger.debug(f"[HEALTH] click filter installed on viewport")

    def _uninstall_click_filter(self):
        """
        Remove the event filter from the scene's viewport.

        Called synchronously on departure while the scene is still valid.
        Also called from purge_session_items step 5 before batch removal.
        Idempotent — safe to call if nothing is installed.
        """
        if self._click_filter is None:
            return
        if self.scene() and self.scene().views():
            self.scene().views()[0].viewport().removeEventFilter(self._click_filter)
        self._click_filter = None
        logger.debug(f"[HEALTH] click filter uninstalled from viewport")

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
            ── footer ── "polling every Ns  ·  filter active/inactive"

        All values read from instance state set by _poll_gc and _SceneClickFilter.
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
            ("Living nodes",  str(self._living_nodes),              node_color),
            ("Scene nodes",   str(self._scene_nodes),               node_color),
            ("RAM delta",     delta_str,                             delta_color),
            ("Last click",    self._last_clicked_type,               Theme.textPrimary),
            ("  └ identity",  self._last_clicked_item,               self.COLOR_LABEL),
            ("GC time",       f"{self._last_gc_time * 1000:.1f}ms",  Theme.textPrimary),
            ("Poll #",        str(self._poll_count),                 self.COLOR_LABEL),
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
        filter_status = "filter ✅" if self._click_filter is not None else "filter ⬜"
        painter.drawText(int(x), int(y), int(w), line_h,
                         Qt.AlignCenter,
                         f"every {interval_s:.0f}s  ·  {filter_status}")

    # ─────────────────────────────────────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────────────────────────────────────

    def itemChange(self, change, value):
        """
        Traffic director for HealthNode scene transitions.

        Arrival (ItemSceneHasChanged, value is not None):
            Installs the click filter synchronously — no timer, no deferred
            callback. The viewport is valid at ItemSceneHasChanged time.

        Departure (ItemSceneChange, value is None):
            Stops the poll timer and uninstalls the click filter immediately,
            while the scene is still valid. BaseNode._prepare_for_removal fires
            via super() and handles connection cleanup.

        Always delegates to super() — BaseNode.itemChange handles _prepare_for_removal
        on departure. Skipping super() here would break the session independence
        contract established in BaseNode. This is not optional.
        """
        # Guard — itemChange can fire during super().__init__() before our
        # own __init__ has run. Check for our attributes before using them.
        if not hasattr(self, '_click_filter'):
            return super().itemChange(change, value)

        logger.log(
            TRACE,
            f"[HEALTH] itemChange — change={change} value={'scene' if value is not None else 'None'} "
            f"filter={'installed' if self._click_filter else 'none'} timer_active={self._poll_timer.isActive()}"
        )

        if change == self.GraphicsItemChange.ItemSceneChange:
            if value is None:
                # Departing — clean up while scene is still valid
                logger.debug(
                    f"[HEALTH] leaving scene — stopping poll timer and uninstalling filter "
                    f"after {self._poll_count} polls"
                )
                self._poll_timer.stop()
                self._uninstall_click_filter()
                logger.debug(f"[HEALTH] departure cleanup complete")

        elif change == self.GraphicsItemChange.ItemSceneHasChanged:
            if value is not None:
                # Fully arrived — scene and viewport are now ready
                logger.debug(f"[HEALTH] entered scene — installing click filter")
                self._install_click_filter()

        result = super().itemChange(change, value)
        logger.log(TRACE, f"[HEALTH] itemChange — super() returned, delegating result")
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # SERIALIZATION
    # ─────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Health state is always live — only structural identity is serialized.

        Readings (_living_nodes, _scene_nodes, _last_gc_time, click filter state)
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
