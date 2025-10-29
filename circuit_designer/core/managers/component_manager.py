"""Component Manager - Handles component operations, placement, and selection"""

from circuit_designer.components import ComponentItem
from circuit_designer.project.undo_commands import RotateComponentCommand


class ComponentManager:
    """Manages component selection, placement, conflict checking, and properties"""

    def __init__(self, scene, graphics_view, inspect_panel, log_panel, undo_stack, backend_simulator):
        """
        Initialize ComponentManager

        Args:
            scene: The QGraphicsScene
            graphics_view: The graphics view (for grid_spacing and grid_rect)
            inspect_panel: InspectPanel for showing component details
            log_panel: LogPanel for logging messages
            undo_stack: QUndoStack for undo/redo support
            backend_simulator: BackendSimulator for parsing values
        """
        self.scene = scene
        self.graphics_view = graphics_view
        self.inspect_panel = inspect_panel
        self.log_panel = log_panel
        self.undo_stack = undo_stack
        self.backend_simulator = backend_simulator
        self.selected_component = None

    def on_component_selected(self, component):
        """Handle component selection"""
        self.selected_component = component
        self.inspect_panel.update_component_data(component)
        self.log_panel.log_message(f"[INFO] {component.component_type} selected")

        conflict = self.check_position_conflict(component)
        if conflict:
            self.log_panel.log_message(f"[WARN] Position {component.get_display_grid_position()} already occupied")

    def check_position_conflict(self, component):
        """Return True if another component already occupies any grid cell of this component's footprint."""
        if not hasattr(component, 'get_occupied_grid_cells'):
            return False
        footprint = component.get_occupied_grid_cells()
        for item in self.scene.items():
            if item is component:
                continue
            if hasattr(item, 'get_occupied_grid_cells'):
                other_cells = item.get_occupied_grid_cells()
                if footprint & other_cells:
                    return True
        return False

    def find_free_grid_position(self, start_gpos, new_component):
        """Find nearest anchor grid (gx, gy) so that the entire footprint (occupied cells)
        does not overlap with existing components. Uses spiral search outwards from start.
        start_gpos: (gx, gy) anchor grid coordinate (as per get_display_grid_position()).
        Returns (gx, gy) or None if no free position found within bounds.
        """
        if not hasattr(new_component, 'get_occupied_grid_cells') or not hasattr(new_component, 'compute_effective_cell_dimensions'):
            return None
        if not hasattr(self.graphics_view, 'grid_rect') or not self.graphics_view.grid_rect:
            return None
        g_left, g_top, g_w, g_h = self.graphics_view.grid_rect
        g = self.graphics_view.grid_spacing
        # Convert scene coords to grid index range (using round consistent with snapping centers)
        min_gx = int(round(g_left / g))
        max_gx = int(round((g_left + g_w) / g))
        min_gy = int(round(g_top / g))
        max_gy = int(round((g_top + g_h) / g))

        # Build occupied cell set of existing components
        occupied = set()
        for item in self.scene.items():
            if item is new_component:
                continue
            if hasattr(item, 'get_occupied_grid_cells'):
                occupied |= item.get_occupied_grid_cells()

        start_x, start_y = start_gpos
        eff_w, eff_h = new_component.compute_effective_cell_dimensions()

        def footprint_free(ax, ay):
            # Construct footprint at anchor (ax, ay)
            cells = new_component.get_occupied_grid_cells(base_gx=ax, base_gy=ay)
            # Boundaries: ensure each cell lies within grid index rectangle
            for cx, cy in cells:
                if cx < min_gx or cx > max_gx or cy < min_gy or cy > max_gy:
                    return False
            # Overlap check
            return not (cells & occupied)

        # Test start first
        if footprint_free(start_x, start_y):
            return start_x, start_y

        # Spiral search
        for radius in range(1, 40):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue  # perimeter only
                    ax = start_x + dx
                    ay = start_y + dy
                    if footprint_free(ax, ay):
                        return ax, ay
        return None

    def on_inspect_field_changed(self):
        """Handle changes in inspect panel fields"""
        if self.selected_component and hasattr(self.selected_component, 'component_type'):
            # Update component properties based on inspect panel values
            if hasattr(self.inspect_panel, 'editName') and self.inspect_panel.editName.isVisible():
                self.selected_component.name = self.inspect_panel.editName.text()

            # Handle orientation changes from the dropdown
            if hasattr(self.inspect_panel, 'comboOrient') and self.inspect_panel.comboOrient.isVisible():
                current_orientation_text = self.inspect_panel.comboOrient.currentText()
                new_orientation = int(current_orientation_text.replace("°", ""))

                # Only rotate if orientation actually changed
                if new_orientation != self.selected_component.orientation:
                    # Calculate the rotation difference
                    rotation_diff = new_orientation - self.selected_component.orientation

                    # Handle wrapping (e.g., from 270° to 0°)
                    if rotation_diff > 180:
                        rotation_diff -= 360
                    elif rotation_diff < -180:
                        rotation_diff += 360

                    # Apply the rotation with undo support
                    command = RotateComponentCommand(self.selected_component, rotation_diff, f"Rotate {self.selected_component.component_type}")
                    self.undo_stack.push(command)

            # Update component-specific values
            comp_type = self.selected_component.component_type
            if comp_type == "Resistor" and hasattr(self.inspect_panel, 'editResistance'):
                if self.inspect_panel.editResistance.isVisible():
                    self.selected_component.value = self.inspect_panel.editResistance.text()
            elif comp_type == "Vdc" and hasattr(self.inspect_panel, 'editVoltage'):
                if self.inspect_panel.editVoltage.isVisible():
                    self.selected_component.value = self.inspect_panel.editVoltage.text()
            elif comp_type == "Switch" and hasattr(self.inspect_panel, 'comboSwitchState'):
                if self.inspect_panel.comboSwitchState.isVisible():
                    self.selected_component.value = self.inspect_panel.comboSwitchState.currentText()
            elif comp_type == "LED":
                # Update LED threshold if changed
                if hasattr(self.inspect_panel, 'editLEDThreshold') and self.inspect_panel.editLEDThreshold.isVisible():
                    threshold_text = self.inspect_panel.editLEDThreshold.text()
                    if threshold_text:
                        # Parse threshold voltage
                        threshold_value = self.backend_simulator.parse_value(threshold_text, 'LED')
                        self.selected_component.led_threshold = threshold_value

    def refresh_all_connection_points(self):
        """Rebuild connection points for all components to adopt latest positioning logic."""
        for item in self.scene.items():
            if isinstance(item, ComponentItem):
                # Preserve existing wires mapping by storing wires per point_id
                saved_wires = {}
                for cp in getattr(item, 'connection_points', []):
                    if hasattr(cp, 'connected_wires'):
                        saved_wires[cp.point_id] = cp.connected_wires[:]
                item.remove_connection_points()
                item.create_connection_points()
                # Attempt to reattach wires to matching point_ids
                for cp in item.connection_points:
                    if cp.point_id in saved_wires:
                        for wire in saved_wires[cp.point_id]:
                            # Update wire endpoints if they referenced old point
                            if hasattr(wire, 'start_point') and wire.start_point.point_id == cp.point_id:
                                wire.start_point = cp
                            if hasattr(wire, 'end_point') and wire.end_point.point_id == cp.point_id:
                                wire.end_point = cp
                            cp.connected_wires.append(wire)
                            wire.update_position()
        self.log_panel.log_message("[INFO] Connection points refreshed for all components")

    def clear_selection(self):
        """Clear component selection"""
        self.selected_component = None
        self.inspect_panel.show_default_state()

    def get_selected_component(self):
        """Get the currently selected component"""
        return self.selected_component
