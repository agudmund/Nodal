#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - check_sessions.py session validator
-Side utility that validates the format of specific json files for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import json
from pathlib import Path

# Constants for easy adjustment later
BOUNDS_THRESHOLD = 10_000

def check_sessions():
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        print(f"Error: '{sessions_dir}' directory not found.")
        return

    total_files = 0
    total_nodes = 0
    flagged_files = []

    for session_file in sorted(sessions_dir.glob("*.json")):
        total_files += 1
        try:
            # The "Silver Bullet" for Windows encoding errors
            with session_file.open(mode="r", encoding="utf-8") as f:
                data = json.load(f)

            nodes = data.get("nodes", [])
            if not nodes:
                print(f"[-] {session_file.name:40} | EMPTY")
                continue

            # Extract positions
            pos_x = [n.get("pos_x", 0) for n in nodes]
            pos_y = [n.get("pos_y", 0) for n in nodes]

            min_x, max_x = min(pos_x), max(pos_x)
            min_y, max_y = min(pos_y), max(pos_y)

            total_nodes += len(nodes)

            # --- Sanity Check Logic ---
            out_of_bounds = any(abs(v) > BOUNDS_THRESHOLD for v in pos_x + pos_y)
            status_flag = " [!] OUT OF BOUNDS" if out_of_bounds else ""
            if out_of_bounds:
                flagged_files.append(session_file.name)

            viewport = data.get("viewport", {})
            scale = viewport.get("scale", 1.0)

            print(f"\n{session_file.name}:{status_flag}")
            print(f"  Nodes: {len(nodes)}")
            print(f"  Range X: [{min_x:5.0f} to {max_x:5.0f}] (Δ {max_x - min_x:.0f})")
            print(f"  Range Y: [{min_y:5.0f} to {max_y:5.0f}] (Δ {max_y - min_y:.0f})")
            print(f"  Scale:   {scale:.4f}")

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"\n{session_file.name}: ERROR - {type(e).__name__}")
            flagged_files.append(f"{session_file.name} (Corrupt/Encoding)")

    # --- Final Summary ---
    print("\n" + "="*40)
    print(f"SUMMARY REPORT")
    print(f"Total Files Scanned: {total_files}")
    print(f"Total Nodes Found:   {total_nodes}")
    if flagged_files:
        print(f"Flagged Issues ({len(flagged_files)}):")
        for f in flagged_files:
            print(f"  - {f}")
    else:
        print("All files passed sanity checks.")
    print("="*40)

if __name__ == "__main__":
    check_sessions()
