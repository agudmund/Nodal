from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt
from graphics.scene import NodeScene, enable_blur 
from widgets import CozyButton
from utils.theme import Theme
from utils.logger import setup_logger

logger = setup_logger()

class NodeGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.middle_mouse_pressed = False
        self.last_pan_pos = None
        self.viewport().setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_pressed = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.SizeAllCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.middle_mouse_pressed and self.last_pan_pos:
            delta = event.pos() - self.last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_pos = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.middle_mouse_pressed = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

class NodalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.handle_height = 70
        self._dragging_window = False
        self._drag_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        enable_blur(int(self.winId()))

    def init_ui(self):
        self.setWindowTitle("Nodal")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Draggable Toolbar Container
        self.toolbar_container = QWidget()
        self.toolbar_container.setFixedHeight(self.handle_height)
        self.toolbar_container.setStyleSheet(f"""
            background-color: {Theme.TOOLBAR_BG.name()};
            border-bottom: 1px solid {Theme.TOOLBAR_BORDER.name()};
        """)
        
        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(15, 0, 15, 0)
        
        new_node_btn = CozyButton("New Node")
        new_node_btn.clicked.connect(self.create_new_node)
        toolbar_layout.addWidget(new_node_btn)
        toolbar_layout.addStretch()

        main_layout.addWidget(self.toolbar_container)

        self.scene = NodeScene()
        self.view = NodeGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.centerOn(1000, 1000)
        main_layout.addWidget(self.view)
        
        self.show()

    def create_new_node(self):
        view_center = self.view.mapToScene(self.view.viewport().width() // 2, self.view.viewport().height() // 2)
        self.scene.add_node(view_center.x(), view_center.y(), "New Node")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < self.handle_height:
            self._dragging_window = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_window:
            new_pos = event.globalPosition().toPoint()
            self.move(self.pos() + (new_pos - self._drag_pos))
            self._drag_pos = new_pos
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging_window = False
        super().mouseReleaseEvent(event)