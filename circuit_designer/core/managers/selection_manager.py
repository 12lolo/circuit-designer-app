"""Selection Manager - Handles selection, copy/paste, and deletion operations"""

from PyQt6.QtWidgets import QGraphicsLineItem
from circuit_designer.components import Wire, ComponentItem
from circuit_designer.components.connection_points import ConnectionPoint
from circuit_designer.project.undo_commands import MultiDeleteCommand


class SelectionManager:
    """Manages component/wire selection, copy/paste, and deletion"""

    def __init__(self, scene, graphics_view, inspect_panel, log_panel, undo_stack):
        """
        Initialize SelectionManager

        Args:
            scene: The QGraphicsScene
            graphics_view: The graphics view (for grid_spacing)
            inspect_panel: InspectPanel for updating on selection changes
            log_panel: LogPanel for logging messages
            undo_stack: QUndoStack for undo/redo support
        """
        self.scene = scene
        self.graphics_view = graphics_view
        self.inspect_panel = inspect_panel
        self.log_panel = log_panel
        self.undo_stack = undo_stack
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

        # Collect items and their connected wires for undo
        items_data = []
        processed_wires = set()  # Track wires we've already processed

        for item in selected_items:
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

        if items_data:
            # Create and execute multi-delete command
            command = MultiDeleteCommand(self.scene, items_data, f"Delete {len(items_data)} item(s)")
            self.undo_stack.push(command)

            self.inspect_panel.show_default_state()
            self.log_panel.log_message(f"[INFO] {len(items_data)} item(s) deleted")
            return True
        return False

    def copy_selected(self):
        """Copy selected components to clipboard"""
        selected_items = self.scene.selectedItems()
        components_data = []

        for item in selected_items:
            if hasattr(item, 'component_type'):
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
        """Paste components from clipboard"""
        if not self.clipboard_data:
            self.log_panel.log_message("[INFO] Clipboard is empty")
            return

        # Calculate offset for pasted components (slight offset from originals)
        offset_x = 40  # 1 grid cell
        offset_y = 40

        pasted_count = 0
        for comp_data in self.clipboard_data:
            try:
                # Create new component
                component = ComponentItem(
                    comp_data["type"],
                    comp_data["size_w"],
                    comp_data["size_h"],
                    self.graphics_view.grid_spacing
                )

                # Set properties
                component.name = comp_data["name"] + "_copy"
                component.value = comp_data["value"]
                component.orientation = comp_data["orientation"]

                # Set position with offset
                new_x = comp_data["relative_pos"]["x"] + offset_x
                new_y = comp_data["relative_pos"]["y"] + offset_y
                component.setPos(new_x, new_y)

                # Apply rotation
                if component.orientation:
                    component.rotate_component(0)  # Triggers recreation with orientation

                # Add to scene
                self.scene.addItem(component)
                component.snap_to_grid()

                pasted_count += 1

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Failed to paste component: {e}")

        if pasted_count > 0:
            self.log_panel.log_message(f"[INFO] Pasted {pasted_count} component(s)")

    def get_selected_items(self):
        """Get currently selected items"""
        return self.scene.selectedItems()
