"""Selection Manager - Handles selection, copy/paste, and deletion operations"""

from PyQt6.QtWidgets import QGraphicsLineItem, QMessageBox
from circuit_designer.components import Wire, ComponentItem
from circuit_designer.components.connection_points import ConnectionPoint, BendPoint
from circuit_designer.project.undo_commands import MultiDeleteCommand, PasteComponentsCommand, DeleteBendPointCommand


class SelectionManager:
    """Manages component/wire selection, copy/paste, and deletion"""

    def __init__(self, scene, graphics_view, inspect_panel, log_panel, undo_stack, component_manager):
        """
        Initialize SelectionManager

        Args:
            scene: The QGraphicsScene
            graphics_view: The graphics view (for grid_spacing)
            inspect_panel: InspectPanel for updating on selection changes
            log_panel: LogPanel for logging messages
            undo_stack: QUndoStack for undo/redo support
            component_manager: ComponentManager for position conflict checking
        """
        self.scene = scene
        self.graphics_view = graphics_view
        self.inspect_panel = inspect_panel
        self.log_panel = log_panel
        self.undo_stack = undo_stack
        self.component_manager = component_manager
        self.clipboard_data = None

    def select_all(self):
        """Select all items in the scene"""
        for item in self.scene.items():
            if hasattr(item, 'setSelected'):
                item.setSelected(True)
        self.log_panel.log_message("[INFO] All items selected")

    def deselect_all(self):
        """Deselect all items"""
        self.scene.clearSelection()
        self.inspect_panel.show_default_state()
        self.log_panel.log_message("[INFO] Selection cleared")

    def delete_selected(self):
        """Delete selected components from the scene (with undo support)"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return

        # Collect bend points for undo-able deletion
        bend_points_to_delete = []

        # Collect items and their connected wires for undo
        items_data = []
        processed_wires = set()  # Track wires we've already processed

        for item in selected_items:
            # Handle bend point deletion with undo support
            if isinstance(item, BendPoint):
                parent_wire = getattr(item, 'parent_wire', None)
                if parent_wire and hasattr(parent_wire, 'bend_points'):
                    # Get the index of the bend point for undo restoration
                    try:
                        bend_index = parent_wire.bend_points.index(item)
                        bend_points_to_delete.append((item, parent_wire, bend_index))
                    except ValueError:
                        # Bend point not in list, skip
                        pass
                continue

            # Skip direct deletion of raw connection points (they are owned by components)
            if isinstance(item, ConnectionPoint):
                continue

            # If this is a wire segment, get the parent wire instead
            if isinstance(item, QGraphicsLineItem) and hasattr(item, 'parent_wire'):
                parent_wire = item.parent_wire
                # Skip if we already processed this wire
                if parent_wire in processed_wires:
                    continue
                processed_wires.add(parent_wire)
                item = parent_wire

            # Skip wires we've already processed
            if isinstance(item, Wire) and item in processed_wires:
                continue
            if isinstance(item, Wire):
                processed_wires.add(item)

            connected_wires = []

            # Collect connected wires for components
            if hasattr(item, 'connection_points'):
                for cp in item.connection_points:
                    if hasattr(cp, 'connected_wires'):
                        connected_wires.extend(cp.connected_wires.copy())

            items_data.append((item, connected_wires))

        # Delete bend points with undo support
        if bend_points_to_delete:
            for bend_point, parent_wire, bend_index in bend_points_to_delete:
                command = DeleteBendPointCommand(
                    self.scene,
                    bend_point,
                    parent_wire,
                    bend_index,
                    "Delete Bend Point"
                )
                self.undo_stack.push(command)
            self.log_panel.log_message(f"[INFO] {len(bend_points_to_delete)} bend point(s) deleted")

        # Delete other items (components, wires) with undo support
        if items_data:
            # Create and execute multi-delete command
            command = MultiDeleteCommand(self.scene, items_data, f"Delete {len(items_data)} item(s)")
            self.undo_stack.push(command)

            self.inspect_panel.show_default_state()
            self.log_panel.log_message(f"[INFO] {len(items_data)} item(s) deleted")
            return True

        # Return True if we deleted anything (bend points or other items)
        return len(bend_points_to_delete) > 0 or len(items_data) > 0

    def copy_selected(self):
        """Copy selected components to clipboard"""
        selected_items = self.scene.selectedItems()
        components_data = []

        for item in selected_items:
            # Only copy actual ComponentItem instances, not child items or other graphics items
            if isinstance(item, ComponentItem):
                # Store component data
                components_data.append({
                    "type": item.component_type,
                    "name": getattr(item, 'name', item.component_type),
                    "value": getattr(item, 'value', ''),
                    "orientation": getattr(item, 'orientation', 0),
                    "size_w": getattr(item, 'size_w', 1),
                    "size_h": getattr(item, 'size_h', 1),
                    "relative_pos": {"x": item.x(), "y": item.y()}
                })

        if components_data:
            self.clipboard_data = components_data
            self.log_panel.log_message(f"[INFO] Copied {len(components_data)} component(s)")
        else:
            self.log_panel.log_message("[INFO] No components selected to copy")

    def paste(self):
        """Paste components from clipboard (with undo support)"""
        if not self.clipboard_data:
            self.log_panel.log_message("[INFO] Clipboard is empty")
            return

        grid_spacing = self.graphics_view.grid_spacing
        pasted_components = []  # Track successfully pasted components for undo
        failed_components = []  # Track components that couldn't be placed

        for comp_data in self.clipboard_data:
            try:
                # Create new component
                component = ComponentItem(
                    comp_data["type"],
                    comp_data["size_w"],
                    comp_data["size_h"],
                    grid_spacing
                )

                # Set properties
                component.name = comp_data["name"] + "_copy"
                component.value = comp_data["value"]
                component.orientation = comp_data["orientation"]

                # Calculate initial desired grid position (offset by 1 cell)
                orig_x = comp_data["relative_pos"]["x"]
                orig_y = comp_data["relative_pos"]["y"]

                # Convert to grid coordinates
                desired_gx = int(round(orig_x / grid_spacing)) + 1  # +1 grid cell offset
                desired_gy = int(round(orig_y / grid_spacing)) + 1

                # Temporarily position component to calculate footprint
                component.setPos(desired_gx * grid_spacing, desired_gy * grid_spacing)

                # Apply rotation before finding position (affects footprint)
                if component.orientation:
                    component.rotate_component(0)  # Triggers recreation with orientation

                # Add to scene temporarily to allow collision checking
                self.scene.addItem(component)

                # Find a free position
                free_pos = self.component_manager.find_free_grid_position(
                    (desired_gx, desired_gy),
                    component
                )

                if free_pos:
                    # Position at free grid location
                    free_gx, free_gy = free_pos
                    component.setPos(free_gx * grid_spacing, free_gy * grid_spacing)
                    component.snap_to_grid()
                    pasted_components.append(component)
                else:
                    # No free position found, remove from scene
                    self.scene.removeItem(component)
                    failed_components.append(component.component_type)
                    self.log_panel.log_message(f"[WARN] Could not find free position for {component.component_type}")

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Failed to paste component: {e}")

        # Handle results based on success/failure
        total_attempted = len(self.clipboard_data)

        if not pasted_components and failed_components:
            # All components failed to paste - show error popup
            self.log_panel.log_message(f"[ERROR] No space available on grid to paste {total_attempted} component(s)")
            QMessageBox.warning(
                None,
                "Paste Failed - No Grid Space",
                f"Could not paste {total_attempted} component(s).\n\n"
                f"The grid is full and there is no available space.\n\n"
                f"Try deleting some components or clearing the canvas first.",
                QMessageBox.StandardButton.Ok
            )
        elif pasted_components and failed_components:
            # Some succeeded, some failed - show warning
            self.log_panel.log_message(
                f"[WARN] Only pasted {len(pasted_components)} of {total_attempted} component(s) - "
                f"{len(failed_components)} failed due to insufficient grid space"
            )
            QMessageBox.warning(
                None,
                "Paste Partially Completed",
                f"Successfully pasted {len(pasted_components)} of {total_attempted} component(s).\n\n"
                f"{len(failed_components)} component(s) could not be placed due to insufficient grid space.\n\n"
                f"Try deleting some components to free up space.",
                QMessageBox.StandardButton.Ok
            )

        # If we have successfully positioned components, add them via undo command
        if pasted_components:
            # Remove from scene temporarily (will be re-added by undo command)
            for component in pasted_components:
                if component.scene() == self.scene:
                    self.scene.removeItem(component)

            # Create and push paste command
            command = PasteComponentsCommand(
                self.scene,
                pasted_components,
                f"Paste {len(pasted_components)} component(s)"
            )
            self.undo_stack.push(command)

            self.log_panel.log_message(f"[INFO] Pasted {len(pasted_components)} component(s)")

    def get_selected_items(self):
        """Get currently selected items"""
        return self.scene.selectedItems()
