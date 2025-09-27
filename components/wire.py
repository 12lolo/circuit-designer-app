"""
Wire component for ECis-full application.
Handles connections between components with support for bends and junctions.
"""

from PyQt6.QtWidgets import QGraphicsLineItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor


class Wire(QGraphicsLineItem):
    """A wire connecting two connection points with support for bends and junctions"""
    def __init__(self, start_point, end_point):
        self.start_point = start_point
        self.end_point = end_point
        self.bend_points = []  # List of intermediate points for wire routing
        self.wire_segments = []  # List of line segments that make up the wire

        # Create initial line from start to end
        start_pos = start_point.get_scene_pos()
        end_pos = end_point.get_scene_pos()
        super().__init__(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())

        # Set appearance
        self.setPen(QPen(QColor(0, 0, 255), 3))  # Blue wire, 3 pixels thick

        # Set z-value to render wires under components but above grid
        self.setZValue(10)

        # Make it selectable and focusable
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

        # Add this wire to both connection points
        start_point.connected_wires.append(self)
        end_point.connected_wires.append(self)

        # Store junction points that might be on this wire
        self.junction_points = []

    def mousePressEvent(self, event):
        """Handle wire selection and bend point creation"""
        from .connection_points import BendPoint  # Import here to avoid circular imports

        if event.button() == Qt.MouseButton.LeftButton:
            # Select this wire
            scene = self.scene()
            if scene:
                # Clear other selections
                for item in scene.selectedItems():
                    item.setSelected(False)

                self.setSelected(True)
                self.setFocus()

                # Update main window to show wire is selected
                main_window = scene.views()[0].main_window
                main_window.on_wire_selected(self)

        elif event.button() == Qt.MouseButton.RightButton:
            # Right click creates a bend point
            scene_pos = event.scenePos()
            self.add_bend_point(scene_pos)

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """Handle key events for wire operations"""
        if event.key() == Qt.Key.Key_J:  # J for Junction
            # Add junction point at wire midpoint
            self.add_junction_point()
        elif event.key() == Qt.Key.Key_Delete:
            # Delete this wire
            self.delete_wire()
        else:
            super().keyPressEvent(event)

    def hoverEnterEvent(self, event):
        """Change appearance when hovering"""
        if not self.isSelected():
            self.setPen(QPen(QColor(100, 100, 255), 4))  # Lighter blue, thicker on hover
            for segment in self.wire_segments:
                segment.setPen(QPen(QColor(100, 100, 255), 4))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Return to normal appearance when not hovering"""
        if not self.isSelected():
            self.setPen(QPen(QColor(0, 0, 255), 3))  # Back to normal
            for segment in self.wire_segments:
                segment.setPen(QPen(QColor(0, 0, 255), 3))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """Handle selection changes"""
        if change == QGraphicsLineItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Selected
                self.setPen(QPen(QColor(255, 0, 0), 4))  # Red and thicker when selected
                self.setZValue(500)  # Bring to front when selected
                for segment in self.wire_segments:
                    segment.setPen(QPen(QColor(255, 0, 0), 4))
                    segment.setZValue(500)  # Bring segments to front too
            else:  # Deselected
                self.setPen(QPen(QColor(0, 0, 255), 3))  # Back to blue
                self.setZValue(10)  # Return to normal z-value
                for segment in self.wire_segments:
                    segment.setPen(QPen(QColor(0, 0, 255), 3))
                    segment.setZValue(10)  # Return segments to normal z-value

        return super().itemChange(change, value)

    def add_bend_point(self, scene_pos):
        """Add a bend point to the wire at the specified position"""
        from .connection_points import BendPoint  # Import here to avoid circular imports

        # Create bend point with correct arguments: parent_wire and position
        bend_point = BendPoint(self, scene_pos)
        self.bend_points.append(bend_point)

        # Add to scene
        if self.scene():
            self.scene().addItem(bend_point)

        # Update wire path to include the new bend point
        self.update_wire_path()

        # Log the action using the new log panel
        main_window = self.scene().views()[0].main_window
        if hasattr(main_window, 'log_panel'):
            main_window.log_panel.log_message(f"[INFO] Bendpunt toegevoegd aan draad")

    def add_junction_point(self):
        """Add a junction point at the midpoint of the wire"""
        from .connection_points import JunctionPoint  # Import here to avoid circular imports

        # Calculate midpoint
        line = self.line()
        midpoint = QPointF((line.x1() + line.x2()) / 2, (line.y1() + line.y2()) / 2)

        # Create junction point
        junction = JunctionPoint(midpoint)
        self.junction_points.append(junction)

        # Add to scene
        if self.scene():
            self.scene().addItem(junction)

        # Log the action using the new log panel
        main_window = self.scene().views()[0].main_window
        if hasattr(main_window, 'log_panel'):
            main_window.log_panel.log_message(f"[INFO] Junctiepunt toegevoegd aan draad")

    def delete_wire(self):
        """Delete this wire and clean up connections"""
        # Remove from connection points
        if self.start_point and self in self.start_point.connected_wires:
            self.start_point.connected_wires.remove(self)
        if self.end_point and self in self.end_point.connected_wires:
            self.end_point.connected_wires.remove(self)

        # Remove bend points
        for bend_point in self.bend_points:
            if bend_point.scene():
                bend_point.scene().removeItem(bend_point)

        # Remove junction points
        for junction in self.junction_points:
            if junction.scene():
                junction.scene().removeItem(junction)

        # Remove wire segments
        for segment in self.wire_segments:
            if segment.scene():
                segment.scene().removeItem(segment)

        # Remove main line from scene
        if self.scene():
            self.scene().removeItem(self)

        # Log the action using the new log panel
        main_window = self.scene().views()[0].main_window if self.scene() and self.scene().views() else None
        if main_window and hasattr(main_window, 'log_panel'):
            main_window.log_panel.log_message(f"[INFO] Draad verwijderd")

    def update_wire_path(self):
        """Update the wire path considering bend points"""
        # Remove existing segments
        for segment in self.wire_segments:
            if segment.scene():
                segment.scene().removeItem(segment)
        self.wire_segments.clear()

        if not self.bend_points:
            # Simple straight line - use the main line item
            self.update_position()
            return

        # Create path through bend points
        points = [self.start_point.get_scene_pos()]

        # Sort bend points by their distance from start point (simple routing)
        sorted_bends = sorted(self.bend_points, key=lambda p:
                            (p.pos().x() - points[0].x())**2 + (p.pos().y() - points[0].y())**2)

        # Add bend point positions
        for bend_point in sorted_bends:
            points.append(bend_point.pos())

        # Add end point
        points.append(self.end_point.get_scene_pos())

        # Hide the main line since we're using segments
        self.hide()

        # Create line segments between consecutive points
        for i in range(len(points) - 1):
            start_pt = points[i]
            end_pt = points[i + 1]

            segment = QGraphicsLineItem(start_pt.x(), start_pt.y(), end_pt.x(), end_pt.y())
            segment.setPen(self.pen())  # Use same pen as main wire

            # Set z-value to match main wire (render under components)
            segment.setZValue(10)

            # Make segments selectable and hoverable too
            segment.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable)
            segment.setAcceptHoverEvents(True)

            # Add segment to scene
            if self.scene():
                self.scene().addItem(segment)

            self.wire_segments.append(segment)

    def update_position(self):
        """Update wire position when components are moved"""
        if self.bend_points:
            # Update the routed path
            self.update_wire_path()
        else:
            # Update simple straight line
            start_pos = self.start_point.get_scene_pos()
            end_pos = self.end_point.get_scene_pos()
            self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            self.show()  # Make sure main line is visible for straight wires
