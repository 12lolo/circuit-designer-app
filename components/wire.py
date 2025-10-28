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
        self.bend_points = []  # List of intermediate points for wire routing (BendPoint objects)
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

    def sceneEventFilter(self, watched, event):
        """Filter events from child objects like segments"""
        # Intercept events from segments and handle them at the wire level
        if hasattr(watched, 'parent_wire') and watched.parent_wire is self:
            # Mouse press on segment - select the parent wire instead
            if event.type() == event.Type.GraphicsSceneMousePress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Select this wire, not the segment
                    scene = self.scene()
                    if scene:
                        # Clear other selections
                        for item in scene.selectedItems():
                            item.setSelected(False)

                        # Select the main wire (this will trigger itemChange which highlights all segments)
                        self.setSelected(True)
                        self.setFocus()

                        # Update main window
                        main_window = scene.views()[0].main_window
                        main_window.on_wire_selected(self)

                    return True  # Event handled

                elif event.button() == Qt.MouseButton.RightButton:
                    # Right click on segment - add bend point
                    self.add_bend_point(event.scenePos())
                    return True  # Event handled

            # Hover events on segments - forward to wire
            elif event.type() == event.Type.GraphicsSceneHoverEnter:
                if not self.isSelected():
                    for segment in self.wire_segments:
                        segment.setPen(QPen(QColor(100, 100, 255), 4))
                return True

            elif event.type() == event.Type.GraphicsSceneHoverLeave:
                if not self.isSelected():
                    for segment in self.wire_segments:
                        segment.setPen(QPen(QColor(0, 0, 255), 3))
                return True

        return super().sceneEventFilter(watched, event)

    def keyPressEvent(self, event):
        """Handle key events for wire operations"""
        if event.key() == Qt.Key.Key_Delete:
            # Delete this wire
            self.delete_wire()
        else:
            super().keyPressEvent(event)

    def hoverEnterEvent(self, event):
        """Change appearance when hovering"""
        if not self.isSelected():
            # Only change main wire pen if no bend points (segments handle hover for bent wires)
            if not self.bend_points:
                self.setPen(QPen(QColor(100, 100, 255), 4))  # Lighter blue, thicker on hover
            for segment in self.wire_segments:
                segment.setPen(QPen(QColor(100, 100, 255), 4))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Return to normal appearance when not hovering"""
        if not self.isSelected():
            # Restore appropriate pen based on whether wire has bend points
            if self.bend_points:
                self.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Transparent for bent wires
            else:
                self.setPen(QPen(QColor(0, 0, 255), 3))  # Blue for straight wires
            for segment in self.wire_segments:
                segment.setPen(QPen(QColor(0, 0, 255), 3))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """Handle selection changes"""
        if change == QGraphicsLineItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Selected
                # Keep main wire pen transparent if bent, but set z-value high
                if not self.bend_points:
                    self.setPen(QPen(QColor(255, 0, 0), 4))  # Red and thicker when selected
                self.setZValue(500)  # Bring to front when selected
                # Highlight all segments when wire is selected
                for segment in self.wire_segments:
                    segment.setPen(QPen(QColor(255, 0, 0), 4))
                    segment.setZValue(500)  # Bring segments to front too
                    segment.setSelected(True)  # Visually select segments
            else:  # Deselected
                # Restore appropriate pen and z-value based on whether wire has bend points
                if self.bend_points:
                    self.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Transparent for bent wires
                    self.setZValue(-1)  # Below everything
                else:
                    self.setPen(QPen(QColor(0, 0, 255), 3))  # Blue for straight wires
                    self.setZValue(10)  # Normal z-value
                # Unhighlight all segments when wire is deselected
                for segment in self.wire_segments:
                    segment.setPen(QPen(QColor(0, 0, 255), 3))
                    segment.setZValue(10)  # Return segments to normal z-value
                    segment.setSelected(False)  # Deselect segments

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
            main_window.log_panel.log_message(f"[INFO] Bend point added to wire")


    def delete_wire(self):
        """Delete this wire and clean up connections"""
        # Remove from connection points
        if self.start_point and hasattr(self.start_point, 'connected_wires') and self in self.start_point.connected_wires:
            self.start_point.connected_wires.remove(self)
        if self.end_point and hasattr(self.end_point, 'connected_wires') and self in self.end_point.connected_wires:
            self.end_point.connected_wires.remove(self)

        # Remove bend points
        for bend_point in self.bend_points:
            if bend_point.scene():
                bend_point.scene().removeItem(bend_point)

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
            main_window.log_panel.log_message(f"[INFO] Wire removed")

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

        # Create path: start -> bend points -> end
        points = [self.start_point.get_scene_pos()]

        # Sort bend points by their distance from start point (simple routing)
        sorted_bends = sorted(self.bend_points, key=lambda p:
                            (p.pos().x() - points[0].x())**2 + (p.pos().y() - points[0].y())**2)

        # Add bend point positions
        for bend_point in sorted_bends:
            points.append(bend_point.pos())

        # Add end point
        points.append(self.end_point.get_scene_pos())

        # Make the main line transparent since we're using segments (don't hide it - hidden items can't receive events!)
        self.setPen(QPen(QColor(0, 0, 0, 0), 0))  # Fully transparent pen
        self.setZValue(-1)  # Move below everything so it doesn't interfere visually

        # Create line segments between consecutive points
        for i in range(len(points) - 1):
            start_pt = points[i]
            end_pt = points[i + 1]

            segment = QGraphicsLineItem(start_pt.x(), start_pt.y(), end_pt.x(), end_pt.y())
            # Segments should be visible (blue, 3px thick), not transparent like the main wire
            segment.setPen(QPen(QColor(0, 0, 255), 3))

            # Set z-value to match main wire (render under components)
            segment.setZValue(10)

            # Store reference to parent wire so events can be forwarded
            segment.parent_wire = self

            # Make segments selectable and hoverable but NOT focusable
            # (segments should forward events to parent wire, not receive them directly)
            segment.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
            segment.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsFocusable, False)
            segment.setAcceptHoverEvents(True)

            # Add segment to scene FIRST (event filters require items to be in a scene)
            if self.scene():
                self.scene().addItem(segment)
                # Now install event filter (must be done after adding to scene)
                segment.installSceneEventFilter(self)

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
            # Restore visible pen for straight wires
            if self.isSelected():
                self.setPen(QPen(QColor(255, 0, 0), 4))  # Red if selected
            else:
                self.setPen(QPen(QColor(0, 0, 255), 3))  # Blue normal
            self.setZValue(10)  # Normal z-value for straight wires

    def _update_junction_positions_REMOVED(self):
        """Update all junction points on this wire to their correct positions"""
        if not self.junction_points:
            return

        # For straight wires (no bend points), junctions stay at midpoint
        if not self.bend_points:
            line = self.line()
            midpoint = QPointF((line.x1() + line.x2()) / 2, (line.y1() + line.y2()) / 2)

            for junction in self.junction_points:
                # Store old position to check if it changed
                old_pos = junction.pos()

                # Allow programmatic position update
                if hasattr(junction, '_allow_programmatic_move'):
                    junction._allow_programmatic_move = True

                junction.setPos(midpoint)

                # Snap to grid
                if hasattr(junction, 'snap_to_grid'):
                    junction.snap_to_grid()

                # Disable programmatic move flag
                if hasattr(junction, '_allow_programmatic_move'):
                    junction._allow_programmatic_move = False

                # Update other wires connected to this junction if position changed
                new_pos = junction.pos()
                if (abs(new_pos.x() - old_pos.x()) > 0.1 or abs(new_pos.y() - old_pos.y()) > 0.1):
                    if hasattr(junction, 'connected_wires'):
                        for wire in junction.connected_wires:
                            if wire is not self:  # Don't update ourselves
                                try:
                                    wire.update_position()
                                except:
                                    pass
        else:
            # For wires with bend points, update junctions to nearest segment midpoint
            # For simplicity, place all junctions at the overall midpoint
            # (A more sophisticated approach would maintain relative positions on segments)
            start_pos = self.start_point.get_scene_pos()
            end_pos = self.end_point.get_scene_pos()
            midpoint = QPointF((start_pos.x() + end_pos.x()) / 2, (start_pos.y() + end_pos.y()) / 2)

            for junction in self.junction_points:
                # Store old position
                old_pos = junction.pos()

                # Allow programmatic position update
                if hasattr(junction, '_allow_programmatic_move'):
                    junction._allow_programmatic_move = True

                junction.setPos(midpoint)

                # Snap to grid
                if hasattr(junction, 'snap_to_grid'):
                    junction.snap_to_grid()

                # Disable programmatic move flag
                if hasattr(junction, '_allow_programmatic_move'):
                    junction._allow_programmatic_move = False

                # Update other wires connected to this junction if position changed
                new_pos = junction.pos()
                if (abs(new_pos.x() - old_pos.x()) > 0.1 or abs(new_pos.y() - old_pos.y()) > 0.1):
                    if hasattr(junction, 'connected_wires'):
                        for wire in junction.connected_wires:
                            if wire is not self:  # Don't update ourselves
                                try:
                                    wire.update_position()
                                except:
                                    pass
