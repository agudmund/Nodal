#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - session_manager.py session persistence
-Save and load nodal graphs from JSON session files for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Optional

try:
    from send2trash import send2trash as _send_to_trash
except ImportError:
    _send_to_trash = None

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


def _rotate_session(filepath: str):
    """
    3-slot save rotation — mirrors build.py's rotateAndArchive and logger.py's _rotate_logs.
    On each save: archive → recycle bin, previous → archive, current → previous.
    Backup slots are kept in ./sessions/backup/ — only the live file stays in ./sessions/.
    """
    current    = Path(filepath)
    backup_dir = current.parent / "backup"
    backup_dir.mkdir(exist_ok=True)

    previous = backup_dir / (current.stem + "_previous.json")
    archive  = backup_dir / (current.stem + "_archive.json")

    def _trash(path: Path):
        """Send to recycle bin; fall back to permanent delete if send2trash is unavailable."""
        if _send_to_trash:
            try:
                _send_to_trash(str(path))
                return
            except Exception:
                pass
        path.unlink(missing_ok=True)

    try:
        if archive.exists():
            _trash(archive)
        if previous.exists():
            previous.rename(archive)
        if current.exists():
            current.rename(previous)
    except Exception:
        pass  # Rotation failure is non-fatal — save continues regardless


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

            # 3-slot rollover before writing — matches build.py / logger.py rotation pattern
            _rotate_session(filepath)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"✅ Session saved successfully to {filepath}")
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
