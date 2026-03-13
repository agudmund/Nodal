from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QLinearGradient, QPainter
from PySide6.QtCore import Qt, QPointF
from utils.theme import Theme

# graphics/connection.py

# graphics/connection.py

class Connection(QGraphicsPathItem):
    def __init__(self, start_node, end_node=None):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.floating_point = None 
        
        self.setZValue(-1)
        self.update_path()

    def update_path(self, mouse_pos=None):
        """The single source of truth for the wire geometry."""
        self.floating_point = mouse_pos
        path = QPainterPath()
        
        # Start at Right Socket of source node
        p1 = self.start_node.scenePos() + QPointF(self.start_node.width, self.start_node.height/2)
        
        if self.end_node:
            # Snap to Left Socket of target node
            p2 = self.end_node.scenePos() + QPointF(0, self.end_node.height/2)
        elif self.floating_point:
            # Follow the mouse cursor
            p2 = self.floating_point
        else:
            return

        path.moveTo(p1)
        
        # Calculate Bezier control points for the 'Rubbery' feel
        # We use a horizontal offset (dx) based on the distance between points
        dx = abs(p2.x() - p1.x()) * 0.5
        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)
        self.prepareGeometryChange()

    def paint(self, painter, option, widget):
        # 1. Broad Glow
        painter.setPen(QPen(Theme.WIRE_GLOW, 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(self.path())
        # 2. Sharp Core
        painter.setPen(QPen(Theme.WIRE_CORE, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(self.path())