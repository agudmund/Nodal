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
        self.start_node.connections.append(self)
        if self.end_node:
            self.end_node.connections.append(self)
        
        self.setZValue(-1)
        self.update_path()

    def update_path(self, mouse_pos=None):
        """Gathers the coordinates and draws the 'Rubbery' Bezier."""
        self.floating_point = mouse_pos
        path = QPainterPath()
        
        # 1. Start Point (Output Port of Start Node)
        # Map from node's local right-edge to scene coordinates
        p1 = self.start_node.mapToScene(self.start_node.rect().width(), self.start_node.rect().height()/2)
        
        if self.end_node:
            # 2. End Point (Input Port of Target Node)
            p2 = self.end_node.mapToScene(0, self.end_node.rect().height()/2)
        elif self.floating_point:
            # 3. Floating Point (Mouse position)
            p2 = self.floating_point
        else:
            return

        path.moveTo(p1)
        
        # Calculate 'Rubbery' Tension
        dx = abs(p2.x() - p1.x()) * 0.5
        # Ensure the wire stays 'Springy' even when ports are vertically aligned
        dx = max(dx, 50) 
        
        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)

    def paint(self, painter, option, widget):
        if not self.path(): return

        painter.setRenderHint(QPainter.Antialiasing)
        
        # Pull the colors directly from your Bedrock Theme
        # We use the Core for the Mint (Output) and Glow for the Copper (Input) 
        # Or use specific new variables if you've added them to Theme
        color_start = Theme.WIRE_CORE # Electrical Mint-ish
        color_end = Theme.WIRE_GLOW  # Warm Copper-ish
        
        p1 = self.path().pointAtPercent(0)
        p2 = self.path().pointAtPercent(1)
        
        grad = QLinearGradient(p1, p2)
        grad.setColorAt(0, color_start)
        grad.setColorAt(1, color_end)
        
        # Drawing the "Glow" line first (thicker, lower alpha)
        glow_pen = QPen(grad, 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(self.path())
        
        # Drawing the "Core" line second (thinner, higher alpha)
        core_pen = QPen(QColor(255, 255, 255, 150), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(core_pen)
        painter.drawPath(self.path())