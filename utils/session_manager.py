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
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsView

from utils.logger import setup_logger
import uuid as uuid_module

logger = setup_logger()

def _get_sessions_dir() -> Path:
    """
    Get the absolute path to the sessions directory.

    Works correctly regardless of where the process was launched from.
    Handles both normal script execution and PyInstaller bundles.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / "sessions"


class SessionManager:
    """Manage persistence of nodal graph sessions to/from JSON files.
    Handles session creation, loading, saving, and listing with proper error handling.
    """

    SESSIONS_DIR = "sessions"
    VERSION = "1.0"

    @staticmethod
    def get_available_sessions() -> List[str]:
        """Retrieve list of all saved session file names from the sessions directory.

        Returns:
            List of session names (without .json extension)
        """
        sessions_path = _get_sessions_dir()

        if not sessions_path.exists():
            logger.warning(f"Sessions directory not found at {sessions_path}")
            return []

        session_files = sorted(sessions_path.glob("*.json"))
        return [f.stem for f in session_files]

    @staticmethod
    def get_session_filename(display_name: str) -> str:
        """Get the full absolute filepath for a session by its display name."""
        sessions_dir = _get_sessions_dir()
        return str(sessions_dir / f"{display_name}.json")

    @staticmethod
    def save_session(filepath: str, data: dict):
        """Drive the data to the warehouse and save as JSON."""
        try:
            # Ensure the directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"✅ Session saved successfully to {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")
        

    @staticmethod
    def get_session_data(filepath: str):
        session_data = None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"⚠️ Could not read session file {filepath}: {e}")
            return None
        return session_data
