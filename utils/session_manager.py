#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - session_manager.py session persistence
-Save and load nodal graphs from JSON session files
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
import sys
import json
from graphics.node_types import NodeBase
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsView

from utils.logger import setup_logger

logger = setup_logger()


def _get_sessions_dir() -> Path:
    """
    Get the absolute path to the sessions directory.

    Works correctly regardless of where the process was launched from.
    Handles both normal script execution and PyInstaller bundles.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller EXE
        base_path = Path(sys.executable).parent
    else:
        # Running as a normal script
        base_path = Path(__file__).resolve().parent.parent

    return base_path / "sessions"


class SessionManager:
    """Handle saving and loading of nodal graph sessions to/from JSON files."""

    SESSIONS_DIR = "sessions"
    VERSION = "1.0"

    @staticmethod
    def get_session_filename(display_name: str) -> str:
        """Get the full absolute filepath for a session by its display name."""
        sessions_dir = _get_sessions_dir()
        return str(sessions_dir / f"{display_name}.json")

    @staticmethod
    def get_available_sessions() -> List[str]:
        """Get list of available session names from sessions/ directory."""
        sessions_path = _get_sessions_dir()

        if not sessions_path.exists():
            logger.warning(f"Sessions directory not found at {sessions_path}")
            return []

        # Find all .json files and return them sorted
        session_files = sorted(sessions_path.glob("*.json"))
        # Return just the filenames without .json extension
        return [f.stem for f in session_files]

    @staticmethod
    def save_session(scene, filepath: str, view: Optional[QGraphicsView] = None):
        """
        Save all nodes in the scene to a JSON session file.

        Args:
            scene: The NodeScene containing nodes to save
            filepath: Full path to save the session file
            view: Optional GraphicsView to capture viewport state
        """
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        nodes_data = []
        node_uuids = []

        # Collect all nodes from scene
        for item in scene.items():
            if isinstance(item, NodeBase):
                node_dict = item.to_dict()
                nodes_data.append(node_dict)
                node_uuids.append(item.uuid)

        logger.debug(f"Saving {len(nodes_data)} nodes to session")

        # Build session data
        session_data = {
            "version": SessionManager.VERSION,
            "nodes": nodes_data,
            "node_order": node_uuids,
        }

        # Capture viewport state if view provided
        if view is not None:
            transform = view.transform()
            scale = transform.m11()  # Extract scale from transformation matrix
            center = view.mapToScene(view.viewport().rect().center())

            session_data["viewport"] = {
                "scale": round(scale, 4),
                "center_x": round(center.x(), 2),
                "center_y": round(center.y(), 2),
            }

        # Atomic save using temporary file
        temp_path = f"{filepath}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, filepath)
            logger.info(f"✅ Session saved: {filepath} ({len(nodes_data)} nodes)")
        except Exception as e:
            logger.error(f"❌ Failed to save session {filepath}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    @staticmethod
    def load_session(scene, filepath: str, view: Optional[QGraphicsView] = None) -> Optional[dict]:
        """
        Load nodes from a JSON session file into the scene.

        Args:
            scene: The NodeScene to populate
            filepath: Full path to the session file to load
            view: Optional GraphicsView to restore viewport state

        Returns:
            The loaded session data dict, or None if load failed
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"⚠️ Could not read session file {filepath}: {e}")
            return None

        # Clear existing nodes from scene
        nodes_to_remove = [item for item in scene.items() if isinstance(item, NodeBase)]
        for node in nodes_to_remove:
            scene.removeItem(node)

        # Restore nodes in order
        created_nodes = {}
        # Support both "node_order" and "layout_order" for compatibility
        node_order = session_data.get("node_order") or session_data.get("layout_order", [])
        nodes_data = {nd.get("uuid"): nd for nd in session_data.get("nodes", [])}

        logger.debug(f"Loading session with {len(nodes_data)} nodes defined, node_order: {len(node_order)}")

        # Load nodes in saved order for consistency
        for node_uuid in node_order:
            node_data = nodes_data.get(node_uuid)
            if node_data:
                try:
                    node = NodeBase.from_dict(node_data)
                    scene.addItem(node)
                    created_nodes[node.uuid] = node
                except Exception as e:
                    logger.error(f"❌ Failed to load node {node_uuid}: {e}")
                    continue

        # Update scene bounds
        if created_nodes:
            scene.setSceneRect(scene.itemsBoundingRect())

        # Restore viewport state if available
        if view is not None and "viewport" in session_data:
            vp = session_data["viewport"]
            try:
                view.resetTransform()
                scale = vp.get("scale", 1.0)
                view.scale(scale, scale)
                view.centerOn(QPointF(vp.get("center_x", 0.0), vp.get("center_y", 0.0)))
                view.viewport().update()
            except Exception as e:
                logger.warning(f"Could not restore viewport state: {e}")

        logger.info(f"✅ Session loaded: {filepath} ({len(created_nodes)} nodes)")
        return session_data
