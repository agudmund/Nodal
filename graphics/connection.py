from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QLinearGradient, QPainter
from PySide6.QtCore import Qt, QPointF
from utils.theme import Theme

# In connection.py

class Connection(QGraphicsPathItem):
    def __init__(self, start_node, end_node=None): # end_node is now optional
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.floating_point = None # Used for the 'Drag' state
        
        self.setZValue(-1)
        self.update_path()

    def update_floating_pos(self, pos):
        """Used when dragging a new wire from a node."""
        self.floating_point = pos
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        # Start at the Right Socket
        p1 = self.start_node.scenePos() + QPointF(self.start_node.width, self.start_node.height/2)
        
        # Determine where the end is
        if self.end_node:
            # Snap to Left Socket of target
            p2 = self.end_node.scenePos() + QPointF(0, self.end_node.height/2)
        elif self.floating_point:
            # Follow the mouse
            p2 = self.floating_point
        else:
            return

        path.moveTo(p1)
        dx = p2.x() - p1.x()
        
        # Rubbery overshoot math
        elasticity = 0.8
        ctrl1 = QPointF(p1.x() + dx * elasticity, p1.y())
        ctrl2 = QPointF(p2.x() - dx * elasticity, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)
        self.prepareGeometryChange()

    def paint(self, painter, option, widget):
        # 1. The Glow (Broad, faint line)
        glow_pen = QPen(Theme.get_alpha(Theme.ACCENT_NORMAL, 40), 6)
        painter.setPen(glow_pen)
        painter.drawPath(self.path())
        
        # 2. The Nerve (Thin, sharp line)
        # Create a gradient that flows with the connection
        grad = QLinearGradient(self.path().pointAtPercent(0), self.path().pointAtPercent(1))
        grad.setColorAt(0, Theme.ACCENT_NORMAL)
        grad.setColorAt(1, Theme.adjust_brightness(Theme.ACCENT_NORMAL, 0.7))
        
        nerve_pen = QPen(grad, 2)
        painter.setPen(nerve_pen)
        painter.drawPath(self.path())