# Ghost Node Rendering Artifact - Investigation & Fix Report

## Summary
This report documents the full investigation into an intermittent rendering artifact where nodes from a previous session appeared as solid-color ghost duplicates baked into the background layer after switching sessions. The investigation covered multiple diagnostic cycles spanning two sessions, culminating in a definitive root cause isolation via debug log analysis and a targeted two-fix resolution.

---

## Symptom

After switching from one session to another, some nodes from the **previous session** remained visible as solid-color ghost shapes rendered directly onto the background. The functional nodes of the new session appeared on top of these ghosts. The artifact was intermittent — it appeared on some session switches but not all.

---

## Initial Fix Cycle (Stable But Not Resolved)

Three root causes were addressed in the first cycle. These stabilized the most obvious cases but did not fully eliminate the artifact.

### RC1 — DontSavePainterState + Missing save()/restore() in paint()

**Problem:** `NodeGraphicsView` had `QGraphicsView.DontSavePainterState` set. Combined with `WA_TranslucentBackground` and `QGraphicsDropShadowEffect`, this caused painter brush/transform state to leak between items during the rendering pass.

**Fix:** Removed `DontSavePainterState` from `NodeGraphicsView`. Wrapped `BaseNode.paint()` in `painter.save()` / `painter.restore()`. Fixed the LOD gate early-return path to call `painter.restore()` before returning.

**Files:** `main_window.py`, `graphics/BaseNode.py`

---

### RC2 — Synchronous viewport.repaint() During setUpdatesEnabled(False)

**Problem:** `load_session` called `viewport().repaint()` synchronously while `view.setUpdatesEnabled(False)` was still active. Shadow effect offscreen buffers had not been initialized yet, causing node bodies to bake into the background layer on the first paint.

**Fix:** Removed the premature synchronous repaint. Replaced with `QTimer.singleShot(0, viewport.update)` deferred after `setUpdatesEnabled(True)` in the `finally` block, giving Qt time to initialize all effect buffers before the first visible paint.

**Files:** `main_window.py`

---

### RC3 — Missing setZValue(10) in rebuild_from_session

**Problem:** Nodes restored via `rebuild_from_session` were landing at Z=0 instead of Z=10 (the value used by `_register_node` for interactively created nodes). At Z=0, nodes could render behind the fog layer or in an undefined compositing order relative to other items.

**Fix:** Added `new_node.setZValue(10)` for each node after `BaseNode.from_dict()` inside `rebuild_from_session`.

**Files:** `graphics/Scene.py`

---

## Debug Instrumentation Added

After the first cycle confirmed the artifact was still intermittent, targeted debug logging was added across the full rendering pipeline to capture paint ordering and state at runtime.

### Additions

- `BaseNode._paint_debug_count` — per-node counter, throttles logging to first 5 paint calls per node
- `BaseNode.paint()` — logs device type, widget type, world transform, composition mode, effect state for first 5 calls
- `BaseNode.paint()` — LOD gate logs state transitions (enable/disable) only on change
- `NodeGraphicsView._bg_paint_count` — background paint call counter, reset after each session load
- `NodeGraphicsView.drawBackground()` — logs first 15 calls with device, rect, viewport size, scale
- `NodeScene.clear_nodes()` — logs item count and node count before and after removal
- `NodeScene.rebuild_from_session()` — logs per-node rebuild details including effect state and paint count
- `NodalApp.load_session()` — step-by-step logging of each phase (setUpdatesEnabled, clear, rebuild, viewport sync)

**Files:** `graphics/BaseNode.py`, `graphics/Scene.py`, `main_window.py`

---

## Debug Run and Log Analysis

The app was run with `python main.py --debug`. The artifact was reproduced by switching from Cleanup.json to Cozy Times - Copy. The full 277-line log was captured at `logs/nodal.log`.

### Finding 1 — Double clear_nodes() Call

The log revealed `clear_nodes()` was being called twice on every session switch:

```
[LOAD_SESSION] clear_nodes()
[CLEAR_NODES] removing 164 items (27 nodes) from scene   ← load_session explicit call
[CLEAR_NODES] scene cleared and cache invalidated

[LOAD_SESSION] rebuild_from_session()
[CLEAR_NODES] removing 1 items (0 nodes) from scene       ← rebuild_from_session internal call
[CLEAR_NODES] scene cleared and cache invalidated
```

`rebuild_from_session` contained its own `self.clear_nodes()` call at the top, which fired again after `load_session` had already cleared the scene. The second call was mostly harmless (only fog_layer remained), but it fired `invalidate()` and `viewport.update()` mid-rebuild while nodes were actively being added to the scene.

### Finding 2 — Ghost Nodes Painting with No Shadow Effect

The definitive smoking gun was found at log lines 162–163, immediately after the first `[BACKGROUND #0]` of the new Cozy Times - Copy session:

```
[BACKGROUND #0] device=QWidget rect=(-912,603,1535,742) ...
[PAINT #2] node=9(warm)  device=QWidget  effect_enabled=no_effect   ← GHOST
[PAINT #2] node=10(warm) device=QWidget  effect_enabled=no_effect   ← GHOST
[PAINT #0] node=21(bezier) device=QPixmap  effect_enabled=True      ← normal new node
```

Two critical anomalies:

- `device=QWidget` — these nodes were painting directly to the viewport, not into a shadow effect offscreen buffer (all legitimate nodes show `device=QPixmap`)
- `effect_enabled=no_effect` — these nodes had no `QGraphicsDropShadowEffect`
- `_paint_debug_count=2` — their counter was already at 2, meaning they were **old Cleanup session nodes** that had received 2 paint calls during the Cleanup scroll interaction. All newly rebuilt nodes correctly show `_paint_debug_count=0`

This confirmed: nodes 9 and 10 from the Cleanup session **survived `clear_nodes()` and leaked into the new session's render**. Their shadow effect had been stripped (by the `setGraphicsEffect(None)` call in `clear_nodes`) but they were never actually removed from the scene.

---

## Root Cause Analysis

### Why clear_nodes() Left Orphaned Nodes

`clear_nodes()` was iterating `self.items()` which returns **all items in the scene including child items** (ports are `QGraphicsEllipseItem` children of their parent node, created with `super().__init__(..., parent_node)`).

The iteration called `removeItem()` on every non-fog item. When `removeItem()` is called on a **child item** (a port), Qt **unparents the child** rather than removing it from the scene entirely. The unparented port then becomes a standalone top-level scene item. Crucially, this also affects the port's parent node — its child count changes mid-iteration, potentially causing Qt's internal bookkeeping to mistrack the parent node's scene membership.

The result: some parent nodes were left as phantom scene items — still rendered, but with their shadow effects stripped and their `_paint_debug_count` preserved from the previous session.

```python
# BEFORE (broken): iterates all items including ports
all_items = self.items()
for item in all_items:
    if item != self.fog_layer:
        item.setGraphicsEffect(None)
        self.removeItem(item)   # ← calling on a child unparents it, orphaning parent
```

```python
# AFTER (fixed): only removes top-level items; children follow automatically
all_items = self.items()
top_level_items = [i for i in all_items if i.parentItem() is None]
for item in top_level_items:
    if item != self.fog_layer:
        item.setGraphicsEffect(None)
        self.removeItem(item)   # ← safe: ports removed automatically with parent
```

---

## Fixes Applied

### Fix 1 — clear_nodes() Top-Level Items Only

**File:** `graphics/Scene.py` — `clear_nodes()` method

**Change:** Added a filter to restrict removal to top-level items only (`parentItem() is None`). Child items (ports) are removed automatically by Qt when their parent node is removed. This prevents ports from being unparented into orphaned scene items that ghost their parent nodes.

```python
# Before
all_items = self.items()
for item in all_items:
    if item != self.fog_layer:
        item.setGraphicsEffect(None)
        self.removeItem(item)

# After
all_items = self.items()
top_level_items = [i for i in all_items if i.parentItem() is None]
for item in top_level_items:
    if item != self.fog_layer:
        item.setGraphicsEffect(None)
        self.removeItem(item)
```

---

### Fix 2 — Remove Redundant clear_nodes() from rebuild_from_session

**File:** `graphics/Scene.py` — `rebuild_from_session()` method

**Change:** Removed the internal `self.clear_nodes()` call at the top of `rebuild_from_session()`. `load_session()` already guarantees the scene is cleared before calling this method. The redundant call fired `invalidate()` + `viewport.update()` mid-rebuild, creating an unnecessary render burst while nodes were actively being added.

```python
# Before
def rebuild_from_session(self, data):
    from graphics.Connection import Connection
    self.clear_nodes()   # ← redundant second clear
    node_map = {}
    ...

# After
def rebuild_from_session(self, data):
    from graphics.Connection import Connection
    # NOTE: load_session already calls clear_nodes() before invoking this method.
    node_map = {}
    ...
```

---

---

## Regression — Nodes From Previous Session Appearing in New Session

After the Fix 1 and Fix 2 commits, a new symptom appeared: nodes from the outgoing session were now rendering as **fully-formed visible nodes** inside the new session (not blank color ghosts — actual styled nodes with text and effects intact). This was a regression introduced by the `setGraphicsEffect(None)` strip in `clear_nodes`.

### Regression Diagnosis

A post-clear survivor log was added to verify whether items were actually leaving the scene:

```
[CLEAR_NODES] scene cleared — 0 survivors (expected 0)
```

The scene confirmed **zero survivors** after every `clear_nodes()` call. The nodes were being removed. Yet ghost paints of previous-session nodes appeared immediately on `[BACKGROUND #0]` of the new session with `device=QWidget` and `effect_enabled=no_effect`.

The key: the ghost nodes had `_paint_debug_count` values matching their **previous-session paint history** (e.g. `count=2` after two Cleanup scroll interactions). This proved the paint calls were not new objects — they were **deferred paint calls for removed objects firing after removal**.

### Regression Root Cause — setGraphicsEffect(None) Schedules a Deferred Paint

Calling `item.setGraphicsEffect(None)` before `removeItem(item)` triggers a Qt `update()` on the item to redraw after the effect is removed. This schedules a **deferred repaint** into Qt's event queue. When `removeItem` then executes, it removes the item from the scene — but the pending repaint event is already queued. That repaint fires on the next event loop cycle, **after** the item has been removed, causing the node to paint directly onto the viewport painter (since it no longer has a shadow effect buffer to render into).

This is the `device=QWidget` + `effect_enabled=no_effect` signature: the removed item paints onto whatever painter is currently active — which turns out to be the scene's background layer during the new session's first `drawBackground` call.

### Regression Fix — Remove the setGraphicsEffect(None) Pre-Strip

**File:** `graphics/Scene.py` — `clear_nodes()` method

**Change:** Removed the `setGraphicsEffect(None)` call entirely. `removeItem()` destroys the item's effect cleanly as part of scene removal — no pre-stripping is needed. Removing the pre-strip eliminates the phantom deferred repaint event.

```python
# Before (regression cause)
for item in top_level_items:
    if item != self.fog_layer:
        if hasattr(item, 'setGraphicsEffect'):
            item.setGraphicsEffect(None)   # ← schedules deferred repaint BEFORE removal
        self.removeItem(item)

# After (fixed)
for item in top_level_items:
    if item != self.fog_layer:
        self.removeItem(item)              # ← effect destroyed cleanly by Qt
```

### Verification

After this fix, four consecutive session switches across three different sessions produced zero `no_effect` paint entries and zero survivors in the log:

```
[CLEAR_NODES] removing 29 top-level items (27 nodes) from scene
[CLEAR_NODES] scene cleared — 0 survivors (expected 0)
...
[CLEAR_NODES] removing 30 top-level items (22 nodes) from scene
[CLEAR_NODES] scene cleared — 0 survivors (expected 0)
...
[CLEAR_NODES] removing 45 top-level items (30 nodes) from scene
[CLEAR_NODES] scene cleared — 0 survivors (expected 0)
```

---

## Files Modified

| File | Change |
|---|---|
| `graphics/Scene.py` | `clear_nodes()` — top-level-only iteration, removed `setGraphicsEffect(None)` pre-strip |
| `graphics/Scene.py` | `rebuild_from_session()` — removed redundant `self.clear_nodes()` call |
| `graphics/BaseNode.py` | `paint()` — `save()`/`restore()` wrapping, LOD early-return fixed, debug logging |
| `main_window.py` | `NodeGraphicsView` — removed `DontSavePainterState`, added debug logging |
| `main_window.py` | `load_session()` — deferred repaint via `QTimer.singleShot`, step logging |

---

## Git Commits

| Hash | Description |
|---|---|
| Previous session | Initial RC1/RC2/RC3 fixes + debug instrumentation |
| `2ee05d7` | `fix: eliminate ghost node rendering artifact on session switch` |
| `aadf47c` | `fix: remove setGraphicsEffect(None) from clear_nodes to stop phantom paint calls` |

---

## Key Lessons

- `QGraphicsScene.items()` returns **all items including child items**. Never call `removeItem()` on child items directly — Qt unparents them rather than removing them, orphaning the parent.
- `setGraphicsEffect(None)` before `removeItem()` schedules a deferred repaint event that fires after the item is removed — the removed item then paints directly onto the active viewport painter as a ghost. Never pre-strip effects before removal.
- `QGraphicsDropShadowEffect` renders to a `QPixmap` offscreen buffer. Any node painting with `device=QWidget` instead of `device=QPixmap` is bypassing the effect pipeline and painting directly to the viewport — this is the signature of a ghost node.
- `DontSavePainterState` + `WA_TranslucentBackground` + `QGraphicsDropShadowEffect` is a hazardous combination and should be avoided.
- Synchronous `viewport.repaint()` during `setUpdatesEnabled(False)` bypasses effect buffer initialization — always defer with `QTimer.singleShot(0, ...)`.
- `_paint_debug_count` surviving across session switches is a reliable indicator that the object is a leaked/orphaned item rather than a freshly deserialized one.
- `[CLEAR_NODES] scene cleared — 0 survivors` confirming the scene is empty, yet ghost paints still appearing, points to deferred repaint events queued before removal — not to items actually surviving in the scene.
