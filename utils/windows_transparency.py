#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - windows_transparency.py Windows API transparency
# Uses ctypes to enable DWM translucency on Windows via native APIs

import sys
import ctypes
from ctypes import windll, wintypes, c_int, byref


class WindowsTransparency:
    """Handle Windows-specific window transparency via DWM (Desktop Window Manager)."""

    # Windows API constants
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_ROUND = 2

    # For Windows 11 Mica effect (modern backdrop blur)
    DWMWA_SYSTEMBACKDROP_TYPE = 38
    DWMSBT_MAINWINDOW = 4  # Enables translucency

    @staticmethod
    def get_hwnd(qwindow) -> int:
        """Extract native window handle (HWND) from QMainWindow."""
        return int(qwindow.winId())

    @staticmethod
    def enable_dark_mode(hwnd: int) -> bool:
        """Enable dark mode for the window."""
        try:
            value = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                WindowsTransparency.DWMWA_USE_IMMERSIVE_DARK_MODE,
                byref(value),
                ctypes.sizeof(value)
            )
            return True
        except Exception as e:
            print(f"⚠️  Failed to enable dark mode: {e}")
            return False

    @staticmethod
    def enable_rounded_corners(hwnd: int) -> bool:
        """Enable rounded window corners (Windows 11)."""
        try:
            value = c_int(WindowsTransparency.DWMWCP_ROUND)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                WindowsTransparency.DWMWA_WINDOW_CORNER_PREFERENCE,
                byref(value),
                ctypes.sizeof(value)
            )
            return True
        except Exception as e:
            print(f"⚠️  Failed to enable rounded corners: {e}")
            return False

    @staticmethod
    def enable_mica_backdrop(hwnd: int) -> bool:
        """Enable Windows 11 Mica translucent backdrop effect."""
        try:
            # Try Windows 11 Mica effect first
            value = c_int(WindowsTransparency.DWMSBT_MAINWINDOW)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                WindowsTransparency.DWMWA_SYSTEMBACKDROP_TYPE,
                byref(value),
                ctypes.sizeof(value)
            )
            print("✅ Windows 11 Mica effect enabled")
            return True
        except Exception as e:
            print(f"⚠️  Mica effect not available: {e}")
            return False

    @staticmethod
    def enable_blur_behind(hwnd: int) -> bool:
        """Enable blur-behind effect (Windows 10/11 fallback)."""
        try:
            # DWM_BLURBEHIND structure
            class DWM_BLURBEHIND(ctypes.Structure):
                _fields_ = [
                    ("dwFlags", wintypes.DWORD),
                    ("fEnable", wintypes.BOOL),
                    ("hRgnBlur", wintypes.HANDLE),
                    ("fTransitionOnMaximized", wintypes.BOOL),
                ]

            DWM_BB_ENABLE = 0x00000001

            blur_behind = DWM_BLURBEHIND()
            blur_behind.dwFlags = DWM_BB_ENABLE
            blur_behind.fEnable = True
            blur_behind.hRgnBlur = None
            blur_behind.fTransitionOnMaximized = False

            windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, byref(blur_behind))
            print("✅ Blur-behind effect enabled")
            return True
        except Exception as e:
            print(f"⚠️  Blur-behind not available: {e}")
            return False


def apply_transparency(qwindow) -> bool:
    """Apply Windows transparency effects to a QMainWindow."""
    if not sys.platform.startswith('win'):
        print("⚠️  Transparency only supported on Windows")
        return False

    try:
        hwnd = WindowsTransparency.get_hwnd(qwindow)
        print(f"🪟 Window HWND: {hwnd}")

        # Extend DWM frame into client area (enable translucency)
        try:
            # MARGINS structure for DwmExtendFrameIntoClientArea
            class MARGINS(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", wintypes.INT),
                    ("cxRightWidth", wintypes.INT),
                    ("cyTopHeight", wintypes.INT),
                    ("cyBottomHeight", wintypes.INT),
                ]

            margins = MARGINS(-1, -1, -1, -1)  # -1 means extend fully
            windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))
            print("✅ DWM frame extended into client area")
        except Exception as e:
            print(f"⚠️  Failed to extend DWM frame: {e}")

        # Apply effects in order of preference
        WindowsTransparency.enable_dark_mode(hwnd)
        WindowsTransparency.enable_rounded_corners(hwnd)

        # Try Mica (Windows 11) first, then blur (Windows 10 fallback)
        if not WindowsTransparency.enable_mica_backdrop(hwnd):
            WindowsTransparency.enable_blur_behind(hwnd)

        print("✅ Window transparency applied successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to apply transparency: {e}")
        return False
