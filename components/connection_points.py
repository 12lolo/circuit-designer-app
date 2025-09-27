"""
Connection points for ECis-full application.
Handles various types of connection points for components and wires.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPen, QColor, QBrush


class BendPoint(QGraphicsEllipseItem):
    """A draggable point that creates a bend/corner in a wire"""
    def __init__(self, parent_wire, position):
        self.radius = 4
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.parent_wire = parent_wire
        self.dragging = False

        # Set position
        self.setPos(position)

        # Set appearance - small green circle
        self.setBrush(QBrush(QColor(0, 200, 0)))
        self.setPen(QPen(QColor(0, 0, 0), 1))

        # Make it draggable
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Ensure it's on top of other items
        self.setZValue(100)

    def mousePressEvent(self, event):
        """Handle start of dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            # Bring to front while dragging
            self.setZValue(200)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle dragging of bend point"""
        if self.dragging:
            super().mouseMoveEvent(event)
            # Update the parent wire path when this bend point moves
            if self.parent_wire:
                self.parent_wire.update_wire_path()

    def mouseReleaseEvent(self, event):
        """Handle end of bend point dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            # Return to normal z-value
            self.setZValue(100)

        super().mouseReleaseEvent(event)
        # Snap to grid if needed and update wire path
        self.snap_to_grid()
        if self.parent_wire:
            self.parent_wire.update_wire_path()

    def itemChange(self, change, value):
        """Handle position changes during dragging"""
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange and self.dragging:
            # Update wire path during drag
            if self.parent_wire and self.scene():
                # Schedule update after position change is complete
                QTimer.singleShot(0, self.parent_wire.update_wire_path)

        return super().itemChange(change, value)

    def snap_to_grid(self):
        """Snap bend point to nearest grid intersection"""
        # Get grid spacing from the graphics view
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'grid_spacing'):
                grid_spacing = view.grid_spacing
                pos = self.pos()

                # Calculate nearest grid position
                grid_x = round(pos.x() / grid_spacing) * grid_spacing
                grid_y = round(pos.y() / grid_spacing) * grid_spacing
                self.setPos(grid_x, grid_y)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(100, 255, 100)))  # Lighter green on hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 200, 0)))  # Back to green
        super().hoverLeaveEvent(event)


class JunctionPoint(QGraphicsEllipseItem):
    """A junction point where multiple wires can connect"""
    def __init__(self, position):
        self.radius = 6
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.connected_wires = []

        # Set position
        self.setPos(position)

        # Set appearance - black filled circle
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # Set z-value to render junction points above wires but below bend points
        self.setZValue(30)

        # Make it draggable and connectable
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        """Handle junction point clicks for wire connections"""
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.scene().views()[0].main_window
            main_window.on_junction_point_clicked(self)
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(100, 100, 100)))  # Gray on hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 0, 0)))  # Back to black
        super().hoverLeaveEvent(event)

    def highlight(self, highlight=True):
        """Highlight this junction point"""
        if highlight:
            self.setBrush(QBrush(QColor(0, 255, 0)))  # Green when highlighted
        else:
            self.setBrush(QBrush(QColor(0, 0, 0)))  # Black normally

    def get_scene_pos(self):
        """Get the absolute position of this junction point in scene coordinates"""
        return self.pos()


class ConnectionPoint(QGraphicsEllipseItem):
    """A connection point on a component where wires can be attached"""
    def __init__(self, parent_component, pos_x, pos_y, point_id):
        self.radius = 5
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.parent_component = parent_component
        self.point_id = point_id
        self.connected_wires = []  # List of wires connected to this point

        # Set position relative to parent component
        self.setPos(pos_x, pos_y)
        self.setParentItem(parent_component)

        # Set appearance
        self.setBrush(QBrush(QColor(255, 0, 0)))  # Red connection points
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # Make it clickable
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.scene().views()[0].main_window
            main_window.on_connection_point_clicked(self)
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(255, 100, 100)))  # Lighter red on hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.isSelected():
            self.setBrush(QBrush(QColor(255, 0, 0)))  # Back to red
        super().hoverLeaveEvent(event)

    def highlight(self, highlight=True):
        """Highlight this connection point"""
        if highlight:
            self.setBrush(QBrush(QColor(0, 255, 0)))  # Green when highlighted
        else:
            self.setBrush(QBrush(QColor(255, 0, 0)))  # Red normally

    def get_scene_pos(self):
        """Get the absolute position of this connection point in scene coordinates"""
        return self.mapToScene(0, 0)
