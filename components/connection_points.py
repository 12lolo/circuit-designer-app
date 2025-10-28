"""
Connection points for ECis-full application.
Handles various types of connection points for components and wires.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QTimer, QPointF
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
    """A junction point on a wire where an additional wire can branch off (behaves like a draggable bend point)"""
    def __init__(self, parent_wire, position):
        self.radius = 6
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.parent_wire = parent_wire
        self.dragging = False
        self.connected_wires = []  # List of wires connected to this junction
        self._press_pos = None  # Track press position to detect clicks vs drags

        # Set position
        self.setPos(position)

        # Set appearance - black filled circle (larger and different from bend point)
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setPen(QPen(QColor(50, 50, 50), 2))

        # Make it draggable
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Ensure it's on top (above bend points)
        self.setZValue(110)

    def mousePressEvent(self, event):
        """Handle start of dragging or wire connection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self._press_pos = event.scenePos()
            # Bring to front while dragging
            self.setZValue(200)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle dragging of junction point"""
        if self.dragging:
            super().mouseMoveEvent(event)
            # Update the parent wire path when this junction moves
            if self.parent_wire:
                self.parent_wire.update_wire_path()

    def mouseReleaseEvent(self, event):
        """Handle end of junction dragging or wire connection"""
        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = self.dragging
            self.dragging = False
            # Return to normal z-value
            self.setZValue(110)

            # Check if this was a click (no movement) or a drag
            moved = False
            if was_dragging and self._press_pos is not None:
                delta = event.scenePos() - self._press_pos
                moved = (abs(delta.x()) > 5 or abs(delta.y()) > 5)

            if moved:
                # This was a drag - snap to grid and update wire
                self.snap_to_grid()
                if self.parent_wire:
                    self.parent_wire.update_wire_path()
            else:
                # This was a click - handle wire connection
                main_window = self.scene().views()[0].main_window
                main_window.on_junction_point_clicked(self)

            self._press_pos = None

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """Handle position changes during dragging"""
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange and self.dragging:
            # Update wire path during drag
            if self.parent_wire and self.scene():
                # Schedule update after position change is complete
                QTimer.singleShot(0, self.parent_wire.update_wire_path)

        return super().itemChange(change, value)

    def snap_to_grid(self):
        """Snap junction point to nearest grid intersection"""
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
        self.setBrush(QBrush(QColor(80, 80, 80)))  # Lighter gray on hover
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

        # Determine role-based base color
        if point_id == 'in':
            self.base_color = QColor(0, 150, 0)          # green for input
        elif point_id == 'out':
            self.base_color = QColor(220, 140, 0)        # orange for output
        elif point_id in ('pos', 'neg'):
            self.base_color = QColor(180, 0, 180)        # magenta for source terminals
        else:  # terminal or other
            self.base_color = QColor(255, 0, 0)          # red default

        # Set position relative to parent component
        self.setPos(pos_x, pos_y)
        self.setParentItem(parent_component)

        # Set appearance
        self.setBrush(QBrush(self.base_color))
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # NOT selectable (prevent deletion)
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.scene().views()[0].main_window
            main_window.on_connection_point_clicked(self)
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        # Lighten on hover
        c = self.base_color.lighter(130)
        self.setBrush(QBrush(c))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Restore highlight state or base color
        if not self.isSelected():
            self.setBrush(QBrush(self.base_color))
        super().hoverLeaveEvent(event)

    def highlight(self, highlight=True):
        """Highlight this connection point (slightly brighter)"""
        if highlight:
            self.setBrush(QBrush(self.base_color.lighter(170)))
        else:
            self.setBrush(QBrush(self.base_color))

    def get_scene_pos(self):
        """Get the absolute position of this connection point in scene coordinates"""
        return self.mapToScene(0, 0)

    def update_connected_wires(self):
        """Update all wires connected to this connection point"""
        for wire in self.connected_wires:
            if hasattr(wire, 'update_position'):
                wire.update_position()
