#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - build.py application test build
-A minor UI for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import PyInstaller.__main__
import shutil
import os
import subprocess
from pathlib import Path

# --- Configuration ---
APP_NAME = "Nodal"
ENTRY_POINT = "main.py"  # Your launcher
ICON_PATH = "resources/icons/app_icon.ico"  # Optional: change to None if you don't have one
# We'll set a custom log path just for this build test
TEST_LOG_PATH = Path(__file__).parent / "test_logs_folder"

def build_app():

    project_root = Path(__file__).parent
    dist_path = project_root / "dist"
    exe_path = dist_path / f"{APP_NAME}.exe"

    print(f"🚀 Starting build for {APP_NAME}...")

    # 1. Inject the Environment Variable for the build/test session
    # This acts as your $COZYLOG override
    print(f"Settting $COZYLOG to: {TEST_LOG_PATH}")
    os.environ["COZYLOG"] = str(TEST_LOG_PATH.absolute())

    # 2. Cleanup
    print(f"🧹 Cleaning old builds...")
    if dist_path.exists():
        shutil.rmtree(dist_path)

    # Define the PyInstaller arguments
    # 3. PyInstaller Arguments
    args = [
        ENTRY_POINT,
        f'--name={APP_NAME}',
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--clean',
    ]

    # Add data folders ONLY if they contain non-python files (icons, configs, etc.)
    # Example: if you have an 'assets' folder:
    args.append('--add-data=resources;resources')

    # Add icon if it exists
    if ICON_PATH and os.path.exists(ICON_PATH):
        args.append(f'--icon={ICON_PATH}')

    # 4. Execute Build
    print(f"🚀 Building {APP_NAME}.exe...")
    PyInstaller.__main__.run(args)

    # 5. Verification Launch
    if exe_path.exists():
        print(f"\n✨ Success! Launching {APP_NAME}.exe for testing...")
        # We use Popen so the build script can finish while the app stays open
        subprocess.Popen([str(exe_path)])
        print(f"Check '{TEST_LOG_PATH}' to see if the sparkle ✨ arrived safely.")
    else:
        print("\n❌ Build failed. Check the console output above.")


if __name__ == "__main__":
    build_app()