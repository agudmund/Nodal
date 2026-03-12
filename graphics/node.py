from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QLinearGradient, QColor, QPen, QBrush, QPainter, QCursor, QFont
from utils.theme import Theme

class Node(QGraphicsItem):
    # Node dimensions
    DEFAULT_WIDTH = 140
    DEFAULT_HEIGHT = 90
    BORDER_RADIUS = 10

    def __init__(self, x: float, y: float, title: str = "Node"):
        super().__init__()
        self.title = title
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT
        self.border_radius = self.BORDER_RADIUS
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return QRectF(-1, -1, self.width + 2, self.height + 2)

    def paint(self, painter, option, widget):
        # 1. PUNCH THE HOLE
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setBrush(Qt.transparent)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # 2. DRAW THE BODY
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        is_sel = self.isSelected()
        accent = Theme.ACCENT_SELECTED if is_sel else Theme.ACCENT_NORMAL
        
        body_grad = QLinearGradient(0, 0, 0, self.height)
        if is_sel:
            body_grad.setColorAt(0, Theme.get_alpha(accent, 180))
            body_grad.setColorAt(1, QColor(10, 20, 30, 230))
            pen = QPen(accent, 2.5)
        else:
            body_grad.setColorAt(0, Theme.NODE_GRADIENT_TOP)
            body_grad.setColorAt(1, Theme.NODE_GRADIENT_BOTTOM)
            pen = QPen(Theme.NODE_BORDER_NORMAL, 1)

        painter.setBrush(body_grad)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.border_radius, self.border_radius)

        # 3. RIM LIGHT & TEXT
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
        painter.drawLine(self.border_radius, 1, self.width - self.border_radius, 1)

        painter.setFont(QFont("Lato", 11, QFont.Bold))
        # Shadow
        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(1, 1, self.width, self.height, Qt.AlignCenter, self.title)
        # Main
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.drawText(0, 0, self.width, self.height, Qt.AlignCenter, self.title)

    def mousePressEvent(self, event):
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().hoverEnterEvent(event)