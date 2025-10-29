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
        if not self.was_added:
            self.scene.addItem(self.component)
            self.was_added = True
        else:
            # Re-add if previously removed
            self.scene.addItem(self.component)

    def undo(self):
        """Remove component from scene"""
        self.scene.removeItem(self.component)


class DeleteComponentCommand(QUndoCommand):
    """Command for deleting a component from the scene"""

    def __init__(self, scene, component, connected_wires=None, description="Delete Component"):
        super().__init__(description)
        self.scene = scene
        self.component = component
        self.connected_wires = connected_wires or []

    def redo(self):
        """Remove component and its wires"""
        # Remove connected wires
        for wire in self.connected_wires:
            if wire.scene() == self.scene:
                self.scene.removeItem(wire)

        # Remove component
        if self.component.scene() == self.scene:
            self.scene.removeItem(self.component)

    def undo(self):
        """Restore component and its wires"""
        # Restore component
        self.scene.addItem(self.component)

        # Restore wires
        for wire in self.connected_wires:
            self.scene.addItem(wire)


class MoveComponentCommand(QUndoCommand):
    """Command for moving a component"""

    def __init__(self, component, old_pos, new_pos, description="Move Component"):
        super().__init__(description)
        self.component = component
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        """Move to new position"""
        self.component.setPos(self.new_pos)
        # Update connected wires
        if hasattr(self.component, 'connection_points'):
            for cp in self.component.connection_points:
                if hasattr(cp, 'update_connected_wires'):
                    cp.update_connected_wires()

    def undo(self):
        """Move back to old position"""
        self.component.setPos(self.old_pos)
        # Update connected wires
        if hasattr(self.component, 'connection_points'):
            for cp in self.component.connection_points:
                if hasattr(cp, 'update_connected_wires'):
                    cp.update_connected_wires()


class RotateComponentCommand(QUndoCommand):
    """Command for rotating a component"""

    def __init__(self, component, angle, description="Rotate Component"):
        super().__init__(description)
        self.component = component
        self.angle = angle

    def redo(self):
        """Rotate component"""
        self.component.rotate_component(self.angle)

    def undo(self):
        """Rotate back"""
        self.component.rotate_component(-self.angle)


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
        setattr(self.component, self.property_name, self.new_value)
        if hasattr(self.component, 'update'):
            self.component.update()

    def undo(self):
        """Restore old value"""
        setattr(self.component, self.property_name, self.old_value)
        if hasattr(self.component, 'update'):
            self.component.update()


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

    def undo(self):
        """Remove wire from scene"""
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

    def undo(self):
        """Restore wire"""
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


class MultiDeleteCommand(QUndoCommand):
    """Command for deleting multiple items at once"""

    def __init__(self, scene, items_data, description="Delete Items"):
        super().__init__(description)
        self.scene = scene
        self.items_data = items_data  # List of (item, connected_wires) tuples

    def redo(self):
        """Remove all items"""
        from circuit_designer.components.wire import Wire

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

    def undo(self):
        """Restore all items"""
        from circuit_designer.components.wire import Wire

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
