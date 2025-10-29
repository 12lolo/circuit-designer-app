"""Wire Manager - Handles wire creation, connection, and validation"""

from circuit_designer.components import Wire
from circuit_designer.project.undo_commands import AddWireCommand


class WireManager:
    """Manages wire creation, connection point clicks, and wire operations"""

    def __init__(self, scene, inspect_panel, log_panel, undo_stack):
        """
        Initialize WireManager

        Args:
            scene: The QGraphicsScene
            inspect_panel: InspectPanel for showing wire details
            log_panel: LogPanel for logging messages
            undo_stack: QUndoStack for undo/redo support
        """
        self.scene = scene
        self.inspect_panel = inspect_panel
        self.log_panel = log_panel
        self.undo_stack = undo_stack

        # Track connection point selection for wire creation
        self.first_selected_point = None
        self.last_selected_point = None

    def on_connection_point_clicked(self, connection_point):
        """Handle click on a connection point with validation (no out->out)."""
        self.log_panel.log_message(f"[INFO] Connection point {connection_point.point_id} clicked")
        connection_point.highlight(True)

        # Deselect previously highlighted last point if different
        if self.last_selected_point and self.last_selected_point != connection_point:
            self.last_selected_point.highlight(False)
        self.last_selected_point = connection_point

        # If this is the first point, store and wait for second
        if not self.first_selected_point:
            self.first_selected_point = connection_point
            return

        # If same point clicked twice, reset
        if self.first_selected_point == connection_point:
            connection_point.highlight(False)
            self.first_selected_point = None
            self.last_selected_point = None
            return

        # Validate connection
        a = self.first_selected_point
        b = connection_point
        if not self.is_connection_allowed(a, b):
            # Invalid connection: show warning, reset highlights
            a.highlight(False)
            b.highlight(False)
            # Determine specific error message
            pid_a = getattr(a, 'point_id', '')
            pid_b = getattr(b, 'point_id', '')
            parent_a = getattr(a, 'parent_component', None)
            parent_b = getattr(b, 'parent_component', None)

            if parent_a is not None and parent_b is not None and parent_a is parent_b:
                self.log_panel.log_message("[WARN] Invalid connection: cannot connect a component to itself")
            elif pid_a == 'out' and pid_b == 'out':
                self.log_panel.log_message("[WARN] Invalid connection: out -> out is not allowed")
            else:
                self.log_panel.log_message("[WARN] Invalid connection")
            self.first_selected_point = None
            self.last_selected_point = None
            return

        # Create wire if valid (use undo command)
        wire = Wire(a, b)
        command = AddWireCommand(self.scene, wire, a, b, f"Connect Wire")
        self.undo_stack.push(command)

        a.highlight(False)
        b.highlight(False)
        self.log_panel.log_message("[INFO] Wire connected")

        self.first_selected_point = None
        self.last_selected_point = None

    def on_wire_selected(self, wire):
        """Handle wire selection"""
        self.log_panel.log_message("[INFO] Wire selected")
        self.inspect_panel.update_wire_data(wire)

    def is_connection_allowed(self, point_a, point_b):
        """Return True if a wire may connect the two points.
        Rules:
        - Disallow out->out connections
        - Disallow connections within the same component
        """
        pid_a = getattr(point_a, 'point_id', '')
        pid_b = getattr(point_b, 'point_id', '')

        # Block out-out in either order
        if pid_a == 'out' and pid_b == 'out':
            return False

        # Block connections to the same component
        parent_a = getattr(point_a, 'parent_component', None)
        parent_b = getattr(point_b, 'parent_component', None)

        if parent_a is not None and parent_b is not None and parent_a is parent_b:
            return False

        return True

    def find_wires_between_components(self, comp1_name, comp2_name, component_name_mapping):
        """Find all wires connecting two components by their backend names

        Args:
            comp1_name: First component backend name
            comp2_name: Second component backend name
            component_name_mapping: Dict mapping backend names to components

        Returns:
            List of Wire objects connecting the two components
        """
        wires = []

        # First, find the components by matching their backend names
        comp1_items = self._find_components_by_backend_name(comp1_name, component_name_mapping)
        comp2_items = self._find_components_by_backend_name(comp2_name, component_name_mapping)

        if not comp1_items or not comp2_items:
            return wires

        # Find wires connecting any combination of these components
        for wire in self.scene.items():
            if not isinstance(wire, Wire):
                continue

            # Get the wire's endpoints
            start_point = getattr(wire, 'start_point', None)
            end_point = getattr(wire, 'end_point', None)

            if not start_point or not end_point:
                continue

            # Check if wire connects the two components
            start_component = self._get_component_for_point(start_point)
            end_component = self._get_component_for_point(end_point)

            # Check if this wire connects our target components
            if ((start_component in comp1_items and end_component in comp2_items) or
                (start_component in comp2_items and end_component in comp1_items)):
                wires.append(wire)

        return wires

    def _find_components_by_backend_name(self, backend_name, component_name_mapping):
        """Find components in the scene that match a backend component name

        Args:
            backend_name: Backend name to search for
            component_name_mapping: Dict mapping backend names to components

        Returns:
            List of components matching the backend name
        """
        components = []

        # Use the stored mapping if available
        if backend_name in component_name_mapping:
            component = component_name_mapping[backend_name]
            if component in self.scene.items():
                components.append(component)

        return components

    def _get_component_for_point(self, point):
        """Get the component that owns a connection point

        Args:
            point: Connection point

        Returns:
            Component owning the connection point, or None
        """
        # For connection points, get parent component
        parent = getattr(point, 'parent_component', None)
        return parent

    def reset_connection_state(self):
        """Reset wire connection state (useful when clearing selection)"""
        if self.first_selected_point:
            self.first_selected_point.highlight(False)
            self.first_selected_point = None
        if self.last_selected_point:
            self.last_selected_point.highlight(False)
            self.last_selected_point = None
