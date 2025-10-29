"""
Circuit management module for saving, loading, and serializing circuits.
Extracted from MainWindow to reduce complexity.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsScene

from circuit_designer.components import Wire, ComponentItem


class CircuitManager:
    """Manages circuit serialization, deserialization, and file operations."""

    def __init__(self, scene: QGraphicsScene, grid_spacing: float):
        self.scene = scene
        self.grid_spacing = grid_spacing

    def serialize_circuit(self) -> Dict[str, Any]:
        """
        Serialize the current circuit to a dictionary.

        Returns:
            Dictionary containing circuit data
        """
        circuit_data = {
            "version": "1.0",
            "components": [],
            "wires": []
        }

        # Collect all components and wires
        for item in self.scene.items():
            if hasattr(item, 'component_type'):
                component_data = {
                    "type": item.component_type,
                    "name": getattr(item, 'name', item.component_type),
                    "value": getattr(item, 'value', ''),
                    "position": {
                        "x": item.x(),
                        "y": item.y()
                    },
                    "orientation": getattr(item, 'orientation', 0),
                    "size": {
                        "width": getattr(item, 'size_w', 1),
                        "height": getattr(item, 'size_h', 1)
                    }
                }
                circuit_data["components"].append(component_data)

            elif isinstance(item, Wire):
                start_point = item.start_point
                end_point = item.end_point

                wire_data = {
                    "start": {
                        "x": start_point.scenePos().x(),
                        "y": start_point.scenePos().y(),
                        "component_id": self._get_component_id(start_point)
                    },
                    "end": {
                        "x": end_point.scenePos().x(),
                        "y": end_point.scenePos().y(),
                        "component_id": self._get_component_id(end_point)
                    }
                }
                circuit_data["wires"].append(wire_data)

        return circuit_data

    def deserialize_circuit(self, circuit_data: Dict[str, Any]) -> bool:
        """
        Load circuit from dictionary data.

        Args:
            circuit_data: Dictionary containing circuit data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear current scene (keep grid)
            for item in list(self.scene.items()):
                if hasattr(item, 'data') and item.data(0) in ('grid', 'grid-border'):
                    continue  # Keep grid items
                self.scene.removeItem(item)

            component_map = {}

            # Load components
            for comp_data in circuit_data.get("components", []):
                component = self._create_component_from_data(comp_data)
                if component:
                    self.scene.addItem(component)

                    # Store in map for wire reconstruction
                    component_id = f"{comp_data['type']}_{comp_data['position']['x']}_{comp_data['position']['y']}"
                    component_map[component_id] = component

            # Load wires
            for wire_data in circuit_data.get("wires", []):
                self._create_wire_from_data(wire_data, component_map)

            return True

        except Exception as e:
            print(f"Error deserializing circuit: {e}")
            return False

    def _create_component_from_data(self, comp_data: Dict[str, Any]) -> Optional[ComponentItem]:
        """Create a component from serialized data."""
        try:
            component_type = comp_data["type"]
            size_w = comp_data["size"]["width"]
            size_h = comp_data["size"]["height"]

            component = ComponentItem(component_type, size_w, size_h, self.grid_spacing)

            component.name = comp_data.get("name", component_type)
            component.value = comp_data.get("value", "")
            component.orientation = comp_data.get("orientation", 0)

            pos = comp_data["position"]
            component.setPos(pos["x"], pos["y"])

            # Apply rotation if needed
            if component.orientation:
                component.rotate_component(0)

            return component

        except Exception as e:
            print(f"Error creating component: {e}")
            return None

    def _create_wire_from_data(self, wire_data: Dict[str, Any], component_map: Dict[str, ComponentItem]):
        """Create a wire from serialized data."""
        try:
            start_pos = QPointF(wire_data["start"]["x"], wire_data["start"]["y"])
            end_pos = QPointF(wire_data["end"]["x"], wire_data["end"]["y"])

            start_component_id = wire_data["start"].get("component_id")
            end_component_id = wire_data["end"].get("component_id")

            # Find connection points
            start_point = self._find_connection_point(start_pos, start_component_id, component_map)
            end_point = self._find_connection_point(end_pos, end_component_id, component_map)

            if start_point and end_point:
                wire = Wire(start_point, end_point)
                self.scene.addItem(wire)
                wire.update_position()

        except Exception as e:
            print(f"Error creating wire: {e}")

    def _find_connection_point(self, position: QPointF, component_id: Optional[str], component_map: Dict[str, ComponentItem]):
        """Find connection point at given position."""
        # Try component-specific search first
        if component_id and component_id in component_map:
            component = component_map[component_id]
            if hasattr(component, 'connection_points'):
                # Find closest connection point on this component
                closest_point = None
                min_distance = float('inf')

                for cp in component.connection_points:
                    cp_pos = cp.get_scene_pos()
                    distance = ((cp_pos.x() - position.x())**2 + (cp_pos.y() - position.y())**2)**0.5

                    if distance < min_distance:
                        min_distance = distance
                        closest_point = cp

                if closest_point and min_distance < 20:
                    return closest_point

        # Fallback: search all items
        tolerance = 10
        for item in self.scene.items():
            if hasattr(item, 'get_scene_pos') and hasattr(item, 'connected_wires'):
                item_pos = item.get_scene_pos()
                distance = ((item_pos.x() - position.x())**2 + (item_pos.y() - position.y())**2)**0.5

                if distance < tolerance:
                    return item

        return None

    def _get_component_id(self, connection_point) -> Optional[str]:
        """Get unique identifier for component owning a connection point."""
        if hasattr(connection_point, 'parent_component'):
            component = connection_point.parent_component
            return f"{component.component_type}_{component.x()}_{component.y()}"
        return None
