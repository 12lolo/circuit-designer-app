"""Undo/Redo commands for circuit designer operations"""

from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF
from circuit_designer.components import ComponentItem, Wire


class AddComponentCommand(QUndoCommand):
    """Command for adding a component to the scene"""

    def __init__(self, scene, component, description="Add Component"):
        super().__init__(description)
        self.scene = scene
        self.component = component
        self.was_added = False

    def redo(self):
        """Add component to scene"""
        try:
            if not self.was_added:
                self.scene.addItem(self.component)
                self.was_added = True
            else:
                # Re-add if previously removed
                self.scene.addItem(self.component)
        except RuntimeError:
            # Component C++ object was deleted (e.g., scene cleared)
            pass

    def undo(self):
        """Remove component from scene"""
        try:
            self.scene.removeItem(self.component)
        except RuntimeError:
            # Component C++ object was already deleted
            pass


class DeleteComponentCommand(QUndoCommand):
    """Command for deleting a component from the scene"""

    def __init__(self, scene, component, connected_wires=None, description="Delete Component"):
        super().__init__(description)
        self.scene = scene
        self.component = component
        self.connected_wires = connected_wires or []

    def redo(self):
        """Remove component and its wires"""
        try:
            # Remove connected wires
            for wire in self.connected_wires:
                if wire.scene() == self.scene:
                    self.scene.removeItem(wire)

            # Remove component
            if self.component.scene() == self.scene:
                self.scene.removeItem(self.component)
        except RuntimeError:
            # Component or wires already deleted
            pass

    def undo(self):
        """Restore component and its wires"""
        try:
            # Restore component
            self.scene.addItem(self.component)

            # Restore wires
            for wire in self.connected_wires:
                self.scene.addItem(wire)
        except RuntimeError:
            # Component or wires C++ object deleted
            pass


class MoveComponentCommand(QUndoCommand):
    """Command for moving a component"""

    def __init__(self, component, old_pos, new_pos, description="Move Component"):
        super().__init__(description)
        self.component = component
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        """Move to new position"""
        try:
            self.component.setPos(self.new_pos)
            # Update connected wires
            if hasattr(self.component, 'connection_points'):
                for cp in self.component.connection_points:
                    if hasattr(cp, 'update_connected_wires'):
                        cp.update_connected_wires()
        except RuntimeError:
            # Component C++ object was deleted
            pass

    def undo(self):
        """Move back to old position"""
        try:
            self.component.setPos(self.old_pos)
            # Update connected wires
            if hasattr(self.component, 'connection_points'):
                for cp in self.component.connection_points:
                    if hasattr(cp, 'update_connected_wires'):
                        cp.update_connected_wires()
        except RuntimeError:
            # Component C++ object was deleted
            pass


class RotateComponentCommand(QUndoCommand):
    """Command for rotating a component"""

    def __init__(self, component, angle, description="Rotate Component"):
        super().__init__(description)
        self.component = component
        self.angle = angle

    def redo(self):
        """Rotate component"""
        try:
            self.component.rotate_component(self.angle)
        except RuntimeError:
            # Component C++ object was deleted
            pass

    def undo(self):
        """Rotate back"""
        try:
            self.component.rotate_component(-self.angle)
        except RuntimeError:
            # Component C++ object was deleted
            pass


class ChangePropertyCommand(QUndoCommand):
    """Command for changing component properties"""

    def __init__(self, component, property_name, old_value, new_value, description="Change Property"):
        super().__init__(description)
        self.component = component
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value

    def redo(self):
        """Apply new value"""
        try:
            setattr(self.component, self.property_name, self.new_value)
            if hasattr(self.component, 'update'):
                self.component.update()
        except RuntimeError:
            # Component C++ object was deleted
            pass

    def undo(self):
        """Restore old value"""
        try:
            setattr(self.component, self.property_name, self.old_value)
            if hasattr(self.component, 'update'):
                self.component.update()
        except RuntimeError:
            # Component C++ object was deleted
            pass


class AddWireCommand(QUndoCommand):
    """Command for adding a wire connection"""

    def __init__(self, scene, wire, start_point, end_point, description="Add Wire"):
        super().__init__(description)
        self.scene = scene
        self.wire = wire
        self.start_point = start_point
        self.end_point = end_point

    def redo(self):
        """Add wire to scene"""
        try:
            self.scene.addItem(self.wire)
            # Register wire with connection points
            if hasattr(self.start_point, 'connected_wires') and self.wire not in self.start_point.connected_wires:
                self.start_point.connected_wires.append(self.wire)
            if hasattr(self.end_point, 'connected_wires') and self.wire not in self.end_point.connected_wires:
                self.end_point.connected_wires.append(self.wire)

            # Restore bend points if they exist
            if hasattr(self.wire, 'bend_points'):
                for bend_point in self.wire.bend_points:
                    if bend_point.scene() != self.scene:
                        self.scene.addItem(bend_point)

            # Recreate wire segments if wire has bend points
            if hasattr(self.wire, 'update_wire_path'):
                self.wire.update_wire_path()
        except RuntimeError:
            # Wire or connection points C++ objects were deleted
            pass

    def undo(self):
        """Remove wire from scene"""
        try:
            # Unregister from connection points
            if hasattr(self.start_point, 'connected_wires') and self.wire in self.start_point.connected_wires:
                self.start_point.connected_wires.remove(self.wire)
            if hasattr(self.end_point, 'connected_wires') and self.wire in self.end_point.connected_wires:
                self.end_point.connected_wires.remove(self.wire)

            # Remove bend points
            if hasattr(self.wire, 'bend_points'):
                for bend_point in self.wire.bend_points:
                    if bend_point.scene() == self.scene:
                        self.scene.removeItem(bend_point)

            # Remove wire segments
            if hasattr(self.wire, 'wire_segments'):
                for segment in self.wire.wire_segments:
                    if segment.scene() == self.scene:
                        self.scene.removeItem(segment)

            # Remove main wire
            if self.wire.scene() == self.scene:
                self.scene.removeItem(self.wire)
        except RuntimeError:
            # Wire or connection points C++ objects were deleted
            pass


class DeleteWireCommand(QUndoCommand):
    """Command for deleting a wire"""

    def __init__(self, scene, wire, start_point, end_point, description="Delete Wire"):
        super().__init__(description)
        self.scene = scene
        self.wire = wire
        self.start_point = start_point
        self.end_point = end_point

    def redo(self):
        """Remove wire"""
        try:
            # Unregister from connection points
            if hasattr(self.start_point, 'connected_wires') and self.wire in self.start_point.connected_wires:
                self.start_point.connected_wires.remove(self.wire)
            if hasattr(self.end_point, 'connected_wires') and self.wire in self.end_point.connected_wires:
                self.end_point.connected_wires.remove(self.wire)

            # Remove bend points
            if hasattr(self.wire, 'bend_points'):
                for bend_point in self.wire.bend_points:
                    if bend_point.scene() == self.scene:
                        self.scene.removeItem(bend_point)

            # Remove wire segments
            if hasattr(self.wire, 'wire_segments'):
                for segment in self.wire.wire_segments:
                    if segment.scene() == self.scene:
                        self.scene.removeItem(segment)

            # Remove main wire
            if self.wire.scene() == self.scene:
                self.scene.removeItem(self.wire)
        except RuntimeError:
            # Wire or connection points C++ objects were deleted
            pass

    def undo(self):
        """Restore wire"""
        try:
            self.scene.addItem(self.wire)
            # Re-register with connection points
            if hasattr(self.start_point, 'connected_wires') and self.wire not in self.start_point.connected_wires:
                self.start_point.connected_wires.append(self.wire)
            if hasattr(self.end_point, 'connected_wires') and self.wire not in self.end_point.connected_wires:
                self.end_point.connected_wires.append(self.wire)

            # Restore bend points
            if hasattr(self.wire, 'bend_points'):
                for bend_point in self.wire.bend_points:
                    if bend_point.scene() != self.scene:
                        self.scene.addItem(bend_point)

            # Recreate wire segments
            if hasattr(self.wire, 'update_wire_path'):
                self.wire.update_wire_path()
        except RuntimeError:
            # Wire or connection points C++ objects were deleted
            pass


class MultiDeleteCommand(QUndoCommand):
    """Command for deleting multiple items at once"""

    def __init__(self, scene, items_data, description="Delete Items"):
        super().__init__(description)
        self.scene = scene
        self.items_data = items_data  # List of (item, connected_wires) tuples

    def redo(self):
        """Remove all items"""
        from circuit_designer.components.wire import Wire

        try:
            for item, wires in self.items_data:
                # Remove wires first
                for wire in wires:
                    if wire.scene() == self.scene:
                        # Use wire's delete method to properly clean up segments and bend points
                        if isinstance(wire, Wire):
                            wire.delete_wire()
                        else:
                            self.scene.removeItem(wire)
                # Remove item
                if item.scene() == self.scene:
                    # If item is a wire, use its delete method for proper cleanup
                    if isinstance(item, Wire):
                        item.delete_wire()
                    else:
                        self.scene.removeItem(item)
        except RuntimeError:
            # Items or wires C++ objects were deleted
            pass

    def undo(self):
        """Restore all items"""
        from circuit_designer.components.wire import Wire

        try:
            for item, wires in self.items_data:
                # Restore item
                self.scene.addItem(item)

                # Restore wires with proper bend point and segment handling
                for wire in wires:
                    self.scene.addItem(wire)

                    # If wire is a Wire instance, restore bend points and segments
                    if isinstance(wire, Wire):
                        # Restore bend points
                        if hasattr(wire, 'bend_points'):
                            for bend_point in wire.bend_points:
                                if bend_point.scene() != self.scene:
                                    self.scene.addItem(bend_point)

                        # Recreate wire segments
                        if hasattr(wire, 'update_wire_path'):
                            wire.update_wire_path()
        except RuntimeError:
            # Items or wires C++ objects were deleted
            pass


class PasteComponentsCommand(QUndoCommand):
    """Command for pasting multiple components at once"""

    def __init__(self, scene, components, description="Paste Components"):
        super().__init__(description)
        self.scene = scene
        self.components = components  # List of components that were pasted

    def redo(self):
        """Add all pasted components to scene"""
        try:
            for component in self.components:
                if component.scene() != self.scene:
                    self.scene.addItem(component)
                    # Ensure connection points are visible
                    if hasattr(component, 'connection_points'):
                        for cp in component.connection_points:
                            if cp.scene() != self.scene:
                                self.scene.addItem(cp)
        except RuntimeError:
            # Components C++ objects were deleted
            pass

    def undo(self):
        """Remove all pasted components from scene"""
        try:
            for component in self.components:
                if component.scene() == self.scene:
                    # Remove connection points first
                    if hasattr(component, 'connection_points'):
                        for cp in component.connection_points:
                            if cp.scene() == self.scene:
                                self.scene.removeItem(cp)
                    # Remove component
                    self.scene.removeItem(component)
        except RuntimeError:
            # Components C++ objects were deleted
            pass


class DeleteBendPointCommand(QUndoCommand):
    """Command for deleting a bend point from a wire"""

    def __init__(self, scene, bend_point, parent_wire, bend_index, description="Delete Bend Point"):
        super().__init__(description)
        self.scene = scene
        self.bend_point = bend_point
        self.parent_wire = parent_wire
        self.bend_index = bend_index  # Position in the bend_points list

    def redo(self):
        """Remove bend point from wire"""
        try:
            # Remove from parent wire's bend_points list
            if hasattr(self.parent_wire, 'bend_points'):
                if self.bend_point in self.parent_wire.bend_points:
                    self.parent_wire.bend_points.remove(self.bend_point)

            # Remove from scene
            if self.bend_point.scene() == self.scene:
                self.scene.removeItem(self.bend_point)

            # Update wire path to make it straight (or follow remaining bend points)
            if hasattr(self.parent_wire, 'update_wire_path'):
                self.parent_wire.update_wire_path()
        except RuntimeError:
            # Bend point or wire C++ objects were deleted
            pass

    def undo(self):
        """Restore bend point to wire"""
        try:
            # Add back to scene
            if self.bend_point.scene() != self.scene:
                self.scene.addItem(self.bend_point)

            # Insert back into parent wire's bend_points list at the original position
            if hasattr(self.parent_wire, 'bend_points'):
                # Make sure we don't exceed list bounds
                insert_pos = min(self.bend_index, len(self.parent_wire.bend_points))
                self.parent_wire.bend_points.insert(insert_pos, self.bend_point)

            # Update wire path to show the bend again
            if hasattr(self.parent_wire, 'update_wire_path'):
                self.parent_wire.update_wire_path()
        except RuntimeError:
            # Bend point or wire C++ objects were deleted
            pass
