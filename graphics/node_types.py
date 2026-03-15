#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - node_types.py specialized node implementations
-Type-specific node classes with QGraphicsTextItem, emoji, resizing, and rich rendering
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import uuid as _uuid
import random
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QSizeF, QAbstractAnimation, QTimer
from PySide6.QtGui import QColor, QPen, QFont, QPainter, QBrush, QFontMetrics, QTextDocument, QPainterPath, QTransform
from utils.theme import Theme
from utils.logger import setup_logger
from . import Port
logger = setup_logger()


class NodeBase(QGraphicsRectItem):
    """Base class for all node types with resize, ports, animations, and rich rendering."""

    def __init__(self, node_id, title, full_text, pos=QPointF(0, 0), width=300, height=200, uuid=None):
        super().__init__(0, 0, width, height)

        self.ports_visible = False # Default
        self.connections = []
    
        # Look at the ledger and manifest the ports if needed
        QTimer.singleShot(0, self._sync_port_visibility)
        
        self.setPos(pos)

        # Identification
        self.node_id = node_id
        self.title = title
        self.full_text = full_text
        self.uuid = uuid or _uuid.uuid4().hex
        self.node_type = "node"

        # Resize handling
        self._resize_handle_size = 12
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_rect = QRectF()

        # Drag tracking
        self._last_scene_pos = pos

        # Port management
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.connections = [] # Ledger for attached wires
        self.ports_visible = False
        self.input_port = None
        self.output_port = None
        self._port_anim = None
        self._create_ports()

        # Hover animation
        self.pulse_anim = QVariantAnimation()
        pulse_duration = random.randint(400, 600)
        self.pulse_anim.setDuration(pulse_duration)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(1.025)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.pulse_anim.valueChanged.connect(self.setScale)

        # Pen styling
        self.normal_pen = QPen(QColor("#444444"), 2)
        self.hover_pen = QPen(self.normal_pen.color().lighter(125), 2)
        self.current_pen = self.normal_pen

        # UI State
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | 
            QGraphicsRectItem.ItemIsSelectable | 
            QGraphicsRectItem.ItemSendsGeometryChanges |
            QGraphicsRectItem.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        # Visuals
        self.setBrush(QColor(30, 30, 30, 200))
        self.round_radius = 18
        self.setPen(self.current_pen)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)

        self.setTransformOriginPoint(self.rect().center())

    def itemChange(self, change, value):
        """
        THE CENTRAL NERVE HUB
        Combines Geometry, Dirty Flags, and IK Kinematics.
        """
        # A. THE KINEMATIC LINK: Update wires when node moves
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self, 'connections'):
                for conn in self.connections:
                    conn.update_path()
            
            # Keep track of last pos for the dirty update
            self._last_scene_pos = self.scenePos()
            if self.scene():
                self.scene().set_dirty(True)

        # B. THE PORT ANCHOR: Keep ports at the edges during resize
        # elif change == QGraphicsRectItem.GraphicsItemChange.ItemScaleHasChanged:
        #     self._update_port_positions()

        return super().itemChange(change, value)

    def _create_ports(self):
        """Create input and output ports but keep them hidden initially."""
        self.input_port = Port(self, is_output=False)
        self.output_port = Port(self, is_output=True)
        self._update_port_positions()
        self.input_port.hide()
        self.output_port.hide()

    def _update_port_positions(self):
        """Update port positions to be outside the node, centered vertically."""
        rect = self.rect()
        center_y = int(rect.height() - 25)
        self.input_port.setPos(-3, center_y)
        self.output_port.setPos(int(rect.width()) + 3, center_y)

    def toggle_ports(self):
        """Toggle port visibility."""
        self.ports_visible = not self.ports_visible
        self._animate_ports()

    def _animate_ports(self):
        """Smoothly fade ports in/out."""
        if self._port_anim and self._port_anim.state() == QAbstractAnimation.Running:
            self._port_anim.stop()

        if self.ports_visible:
            self.input_port.show()
            self.output_port.show()
        else:
            self.input_port.hide()
            self.output_port.hide()

    def mouseDoubleClickEvent(self, event):
        """
        PURPOSE: Differentiate between 'Thinking' (Left) and 'Connecting' (Right).
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 1. THE THOUGHT EDITOR
            if hasattr(self, "open_editor"):
                self.open_editor()
                event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            # 2. THE NERVE TOGGLE
            # This reveals the Port.py objects so we can start wiring
            self.ports_visible = not self.ports_visible
            
            # We tell the Foreman the scene has changed
            if self.scene():
                self.scene().set_dirty(True)
                
            # Visually update the ports immediately
            self._sync_port_visibility()
            event.accept()

    def _sync_port_visibility(self):
        # Clear existing ports (Standard Cleanup)
        existing_ports = [item for item in self.childItems() if isinstance(item, Port)]
        for p in existing_ports:
            self.scene().removeItem(p)

        if self.ports_visible:
            # 1. Output (Mint) - Always visible if toggled
            self.output_port = Port(self, is_output=True)
            self.output_port.setPos(self.rect().width(), self.rect().height() / 2)
            
            # 2. Input (Copper) - Only visible if it has a nerve attached
            has_incoming = any(c.end_node == self for c in self.connections)
            if has_incoming:
                self.input_port = Port(self, is_output=False)
                self.input_port.setPos(0, self.rect().height() / 2)

        def open_editor(self):
            """Open the note editor for this node. Override in subclasses."""
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 1. THE PORT HANDSHAKE (High Priority)
            # We check the scene at the click point, filtering for our child Ports
            click_pos = event.scenePos()
            for child in self.childItems():
                from graphics.port import Port
                if isinstance(child, Port):
                    # Check if the click is physically on the port
                    if child.contains(child.mapFromScene(click_pos)):
                        if getattr(child, 'is_output', False):
                            from graphics.connection import Connection
                            self.temp_connection = Connection(self)
                            self.scene().addItem(self.temp_connection)
                            event.accept()
                            return

            # B. CHECK FOR RESIZE HANDLE (Geometry)
            rect = self.rect()
            # Note: self._resize_handle_size should be defined in __init__ (usually 10-15)
            handle_area = QRectF(
                rect.right() - 20, # Buffer for easier grabbing
                rect.bottom() - 20,
                20, 20
            )
            if handle_area.contains(event.pos()):
                self._is_resizing = True
                self._resize_start_pos = event.pos()
                self._resize_start_rect = self.rect()
                event.accept()
                return

        # C. FALLBACK: Standard Node Dragging
        self._is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """The 'Live' update loop for Wires and Resizing."""
        # 1. LIVE WIRE: Follow the mouse
        # If we are currently growing a nerve, update its destination to the mouse
        if hasattr(self, 'temp_connection') and self.temp_connection:
            self.temp_connection.update_path(event.scenePos())
            event.accept()
            return

        # Fallback to your existing Resize or Drag logic
        super().mouseMoveEvent(event)

        # 2. LIVE RESIZE: Stretch the geometry
        if self._is_resizing:
            delta = event.pos() - self._resize_start_pos
            new_width = max(120, self._resize_start_rect.width() + delta.x())
            new_height = max(50, self._resize_start_rect.height() + delta.y())

            # Support Aspect Ratio Lock
            if event.modifiers() & Qt.ShiftModifier:
                ratio = self._resize_start_rect.width() / self._resize_start_rect.height()
                new_height = new_width / ratio

            self.prepareGeometryChange()
            self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, new_height)))
            self.update() # Triggers the Unified Paint Pipeline
            event.accept()
            return

        # 3. FALLBACK: Drag the node position
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
            """Finalizing the 'Nerve' or the 'Geometry'."""
            # 1. FINALIZE RESIZE
            if self._is_resizing:
                self._is_resizing = False
                self._sync_port_visibility()
                event.accept()

            # 2. FINALIZE CONNECTION
            if hasattr(self, 'temp_connection') and self.temp_connection:
                # THE CANDIDATE SEARCH: Find the node under the release point
                items = self.scene().items(event.scenePos())
                target_node = None
                for item in items:
                    # We want a NodeBase that isn't ourselves
                    if isinstance(item, NodeBase) and item != self:
                        target_node = item
                        break
                
                if target_node:
                    self.temp_connection.end_node = target_node
                    
                    # Register the nerve in both nodes' ledgers
                    if self.temp_connection not in self.connections:
                        self.connections.append(self.temp_connection)
                    if hasattr(target_node, 'connections') and self.temp_connection not in target_node.connections:
                        target_node.connections.append(self.temp_connection)
                    
                    # Force the target to manifest its copper input port
                    target_node._sync_port_visibility()
                    self.temp_connection.update_path()
                    
                    if self.scene():
                        self.scene().set_dirty(True)
                else:
                    # SACRIFICE: No target found, remove the temporary wire
                    self.scene().removeItem(self.temp_connection)
                
                self.temp_connection = None
                event.accept()
                return

            super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        """Trigger a gentle pulse animation on hover."""
        self.current_pen = self.hover_pen
        self.setPen(self.current_pen)
        self.update()

        if self.pulse_anim.state() == QVariantAnimation.Stopped:
            self.pulse_anim.setDirection(QVariantAnimation.Forward)
            self.pulse_anim.start()

            def reverse_pulse():
                if self.pulse_anim.direction() == QVariantAnimation.Forward:
                    self.pulse_anim.setDirection(QVariantAnimation.Backward)
                    self.pulse_anim.start()

            if self.pulse_anim.receivers("finished") > 0:
                self.pulse_anim.finished.disconnect()
            self.pulse_anim.finished.connect(reverse_pulse)

        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Reset pen on hover leave."""
        self.current_pen = self.normal_pen
        self.setPen(self.current_pen)
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget):
        """
        THE UNIFIED PAINT PIPELINE
        PURPOSE: One loop to rule the Shell, the Glow, and the LOD.
        """
        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        rect = self.rect()

        # 1. THE BODY (Always Rounded, Always Prestige)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Selection Glow (No more dotted lines!)
        if self.isSelected():
            painter.setPen(QPen(QColor("#a8d0ff"), 2.5, Qt.SolidLine))
        else:
            painter.setPen(self.pen())
            
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, self.round_radius, self.round_radius)

        # 2. LOD GATEKEEPER
        if lod < 0.3:
            for child in self.childItems():
                # EXCEPTION: If the child is a Port, and it's visible, 
                # we might want to keep it, but for MAXIMUM speed, 
                # let's only hide NON-port items here.
                if not isinstance(child, Port):
                    child.hide()
                else:
                    # Ports stay visible but we stop their expensive glow
                    child.setGraphicsEffect(None) 
                    
            if self.graphicsEffect(): 
                self.graphicsEffect().setEnabled(False)
            return

        # Draw the Resize Handle (The Triangle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        handle_path = QPainterPath()
        handle_path.moveTo(rect.right(), rect.bottom() - 12)
        handle_path.lineTo(rect.right(), rect.bottom())
        handle_path.lineTo(rect.right() - 12, rect.bottom())
        handle_path.closeSubpath()
        painter.drawPath(handle_path)

        # 4. SPECIALIST HANDOFF
        # This is where WarmNode or ImageNode draws their 'Soul'
        self.paint_content(painter)

    def setRect(self, rect):
        """Override to update port positions when node is resized."""
        super().setRect(rect)
        self._update_port_positions()

    def boundingRect(self):
        """Return the full rect including shadow effect margins."""
        shadow_margin = 22
        rect = self.rect()
        return rect.adjusted(-shadow_margin, -shadow_margin, shadow_margin, shadow_margin)

    def paint_content(self, painter):
        """Override this in subclasses to draw text, images, or renders."""
        pass

    def to_dict(self):
        data = {
            "node_id": self.node_id,
            "uuid": self.uuid,
            "type": self.node_type,
            "title": self.title,
            "full_text": self.full_text,
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "width": self.rect().width(),
            "height": self.rect().height(),
            "ports_visible": self.ports_visible  # THE KEY!
        }
        return data

    @staticmethod
    def from_dict(data: dict) -> 'NodeBase':
        """Factory method to create appropriate node type from dictionary."""
        node_type = data.get("type", "node")

        if node_type == "warm":
            return WarmNode.from_dict(data)
        elif node_type == "about":
            return AboutNode.from_dict(data)
        elif node_type == "image":
            return ImageNode.from_dict(data)
        else:
            return NodeBase._create_from_dict(data)

    @staticmethod
    def _create_from_dict(data: dict) -> 'NodeBase':
        """Create base node from dict."""
        node = NodeBase(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Node"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 300),
            height=data.get("height", 200),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class WarmNode(NodeBase):
    """Text/thought node with QGraphicsTextItem, emoji, and note editor."""

    MIN_WIDTH = 180
    MIN_HEIGHT = 60
    MAX_HEIGHT = 1000
    MARGIN = 20

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
        # Calculate minimum width based on title text if width not provided
        if width is None:
            title_font = QFont(Theme.NODE_TITLE_FONT_FAMILY, Theme.NODE_TITLE_FONT_SIZE, QFont.Bold)
            metrics = QFontMetrics(title_font)
            # Title width + emoji (50px) + padding (20px each side) + some breathing room (20px)
            title_width = metrics.horizontalAdvance(title) if title else 0
            width = max(Theme.NODE_WIDTH, title_width + 90)  # 50 emoji + 40 padding/margins

        if height is None:
            height = Theme.NODE_HEIGHT

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "warm"
        self.setBrush(Theme.WARM_NODE_BG)

        # Random emoji for visual personality
        self.emoji = random.choice(["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"])

        # QGraphicsTextItem for emoji
        self.emoji_item = QGraphicsTextItem(self)
        self.emoji_item.setFont(QFont("Segoe UI Emoji", 28))
        self.emoji_item.setPlainText(self.emoji)
        self.emoji_item.setPos(5, 3)

        # QGraphicsTextItem for title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setFont(QFont(Theme.NODE_TITLE_FONT_FAMILY, Theme.NODE_TITLE_FONT_SIZE, QFont.Bold))
        self.title_item.setDefaultTextColor(QColor("#a8d0ff"))

        # QGraphicsTextItem for body text
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont(Theme.NODE_BODY_FONT_FAMILY, Theme.NODE_BODY_FONT_SIZE))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))

        # Layout update timer
        self._layout_timer = QTimer()
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._sync_content_layout)

        # Track if editor is open
        self._editor = None

        self._sync_content_layout()

    def paint_content(self, painter):
        """Specific dialogue for the WarmNode: Emojis and Thoughts."""
        # Since WarmNode uses child QGraphicsTextItems (self.emoji_item, etc.),
        # we just ensure they are visible. Qt draws child items automatically 
        # AFTER the parent's paint() finishes.
        if not self.emoji_item.isVisible():
            self.emoji_item.show()
            self.title_item.show()
            self.text_item.show()

    def setRect(self, rect):
        """Override to sync content layout when resized."""
        super().setRect(rect)
        self._sync_content_layout()

    def _sync_content_layout(self):
        """Update position and visibility of title and body text items."""
        r = self.rect()

        # === Emoji display (top-left) ===
        # (Will be drawn in paint_content instead)

        # === Title positioning ===
        metrics = QFontMetrics(self.title_item.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, r.width() - 80)
        self.title_item.setPlainText(elided_title)
        self.title_item.setPos(60, 9)

        # === Tiny title-card mode (< 95px height) ===
        if r.height() < 95:
            # Hide body text for small nodes
            self.text_item.setVisible(False)
        else:
            # Show body text
            self.text_item.setVisible(True)

            doc = QTextDocument()
            doc.setDefaultFont(self.text_item.font())
            doc.setPlainText(self.full_text)
            doc.setTextWidth(r.width() - (self.MARGIN * 2))

            self.text_item.setDocument(doc)
            self.text_item.setPos(self.MARGIN, 55)

            # Auto-grow height based on content
            content_needed = doc.size().height() + 85
            if content_needed > r.height() + 8:
                final_h = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, content_needed))
                if abs(r.height() - final_h) > 4:
                    self.prepareGeometryChange()
                    self.setRect(QRectF(r.topLeft(), QSizeF(r.width(), final_h)))

        self.update()

    def open_editor(self):
        """Open the sophisticated note editor."""
        from graphics.note_editor import CozyNoteEditor

        # Get the main window
        main_window = None
        for view in self.scene().views():
            main_window = view.window()
            break

        # Create editor dialog (parented to main window for proper cleanup)
        self._editor = CozyNoteEditor(self.node_id, self.title, self.full_text, parent=main_window)

        # Make editor appear on top without flickering - use raise() and activateWindow()
        # This avoids the expensive setWindowFlags() call that causes screen flicker
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()

        # Connect signals
        self._editor.accepted.connect(self._on_editor_accepted)
        self._editor.rejected.connect(self._on_editor_rejected)

        # Show modeless dialog
        self._editor.setModal(False)

    def _on_editor_accepted(self):
        """User clicked Save → apply changes."""
        if self._editor:
            self.title = self._editor.get_title()
            self.full_text = self._editor.get_text()

            # Recalculate width based on new title (same logic as __init__)
            title_font = QFont(Theme.NODE_TITLE_FONT_FAMILY, Theme.NODE_TITLE_FONT_SIZE, QFont.Bold)
            metrics = QFontMetrics(title_font)
            title_width = metrics.horizontalAdvance(self.title) if self.title else 0
            new_width = max(Theme.NODE_WIDTH, title_width + 90)

            # Update node width if it changed
            rect = self.rect()
            if abs(rect.width() - new_width) > 0.1:
                self.prepareGeometryChange()
                self.setRect(QRectF(rect.topLeft(), QSizeF(new_width, rect.height())))

            self._sync_content_layout()
            self.update()
            self._editor.mark_as_saved()
            if self.scene():
                self.scene().update()
            self._close_editor()

    def _on_editor_rejected(self):
        """User clicked Cancel → do nothing."""
        self._close_editor()

    def _close_editor(self):
        """Clean up editor reference."""
        if self._editor:
            del self._editor
            self._editor = None

    @staticmethod
    def from_dict(data: dict) -> 'WarmNode':
        """Deserializes a WarmNode using the standard Warehouse keys."""
        node = WarmNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Warm Node"), # Matches 'title' key
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)), # Matches 'pos_x/y'
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class AboutNode(NodeBase):
    """Meta/information node - smaller, no ports."""

    def __init__(self, node_id=0, title="About", full_text="", pos=QPointF(0, 0), 
                 width=200, height=55, uuid=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "about"
        self.setBrush(Theme.ABOUT_NODE_BG)

    def paint_content(self, painter):
        """Simple text rendering for about nodes."""
        padding = 8
        painter.setPen(Theme.TEXT_PRIMARY)
        painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 10, QFont.Bold))
        painter.drawText(
            padding, padding, 
            self.rect().width() - (padding * 2), self.rect().height() - (padding * 2),
            Qt.TextWordWrap | Qt.AlignCenter, 
            self.title
        )

    @staticmethod
    def from_dict(data: dict) -> 'AboutNode':
        """Create AboutNode from dictionary."""
        node = AboutNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "About"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width", 200),
            height=data.get("height", 55),
            uuid=data.get("uuid")
        )
        node.ports_visible = data.get("ports_visible", False)
        return node


class ImageNode(NodeBase):
    """Image display node - shows image content."""

    def __init__(self, node_id=0, title="", full_text="", pos=QPointF(0, 0), 
                 width=None, height=None, uuid=None):
        if width is None:
            width = 200
        if height is None:
            height = 200

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.node_type = "image"
        self.image = None

    def paint_content(self, painter):
        """Specific dialogue for the ImageNode: Visual Content."""
        if self.image:
            # Draw the image elided within the rounded frame
            painter.drawPixmap(self.rect().toRect(), self.image)
        
        # Draw the caption if it exists
        if self.title:
            painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 8))
            painter.setPen(QColor(200, 200, 200, 150))
            painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter, self.title)

    def paint_content(self, painter):
        """Image nodes: show title as caption if needed."""
        if self.title and len(self.title) > 0:
            painter.setFont(QFont(Theme.BUTTON_FONT_FAMILY, 8))
            painter.setPen(QColor(200, 200, 200, 150))
            painter.drawText(0, self.rect().height() - 15, self.rect().width(), 15, 
                           Qt.AlignCenter, self.title)
    
    @staticmethod
    def from_dict(data: dict) -> 'ImageNode':
        node = ImageNode(
            node_id=data.get("node_id", 0),
            title=data.get("title", "Image Node"),
            full_text=data.get("full_text", ""),
            pos=QPointF(data.get("pos_x", 0), data.get("pos_y", 0)),
            width=data.get("width"),
            height=data.get("height"),
            uuid=data.get("uuid")
        )
        return node
