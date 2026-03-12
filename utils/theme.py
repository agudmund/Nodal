from PySide6.QtGui import QColor

class Theme:
    # --- Primary Branding ---
    ACCENT_NORMAL = QColor("#3498db")
    ACCENT_SELECTED = QColor("#00d2ff")
    TEXT_PRIMARY = QColor("#ffffff")
    
    # --- Window & Toolbar ---
    WINDOW_BG = QColor("#1e1e1e")
    TOOLBAR_BG = QColor("#1a1a1c")
    TOOLBAR_BORDER = QColor("#3a3a3f")
    
    # --- Scene Background ---
    FROST_COLOR = QColor(30, 30, 35, 150)
    GRID_COLOR = QColor(200, 200, 200, 30)

    # --- Node Specifics ---
    NODE_GRADIENT_TOP = QColor(50, 50, 55, 160)
    NODE_GRADIENT_BOTTOM = QColor(20, 20, 25, 210)
    NODE_BORDER_NORMAL = QColor(100, 100, 110, 150)
    
    @staticmethod
    def get_alpha(color: QColor, alpha: int):
        """Helper to quickly swap alpha without hardcoding RGB elsewhere."""
        return QColor(color.red(), color.green(), color.blue(), alpha)

    @staticmethod
    def adjust_brightness(color: QColor, factor: float):
        """
        factor > 1.0 makes it brighter, < 1.0 makes it darker.
        Example: Theme.adjust_brightness(Theme.ACCENT_NORMAL, 0.8) # 20% darker
        """
        r = max(0, min(255, int(color.red() * factor)))
        g = max(0, min(255, int(color.green() * factor)))
        b = max(0, min(255, int(color.blue() * factor)))
        return QColor(r, g, b, color.alpha())

    @staticmethod
    def lerp(color1: QColor, color2: QColor, t: float):
        """Linearly interpolates between two colors (t from 0.0 to 1.0)"""
        r = int(color1.red() + (color2.red() - color1.red()) * t)
        g = int(color1.green() + (color2.green() - color1.green()) * t)
        b = int(color1.blue() + (color2.blue() - color1.blue()) * t)
        a = int(color1.alpha() + (color2.alpha() - color1.alpha()) * t)
        return QColor(r, g, b, a)