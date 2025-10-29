"""Netlist builder for converting circuit to backend-friendly format"""

from typing import Dict, List, Set, Tuple, Optional
from PyQt6.QtWidgets import QGraphicsScene
from circuit_designer.components import Wire, ComponentItem


class NetlistBuilder:
    """Builds a netlist representation from the circuit scene"""

    def __init__(self):
        self.node_counter = 0
        self.node_map = {}  # Map connection points to node IDs
        self.components = []
        self.nodes = {}  # node_id -> list of component connections
        self.ground_node = None

    def build_netlist(self, scene: QGraphicsScene) -> Dict:
        """
        Build a netlist from the scene

        Returns a dictionary with:
        - components: List of component dicts with type, value, nodes
        - nodes: Dict of node_id -> list of connections
        - ground_node: ID of the ground node (if any)
        - errors: List of validation errors
        """
        self.reset()

        # Collect all components and wires
        components = []
        wires = []

        for item in scene.items():
            if hasattr(item, 'component_type'):
                components.append(item)
            elif isinstance(item, Wire):
                wires.append(item)

        # Build connectivity map
        connectivity = self._build_connectivity_map(components, wires)

        # Assign node IDs to connected groups
        self._assign_node_ids(connectivity)

        # Find ground node
        self._find_ground_node(components)

        # Build component list with node connections
        component_list = self._build_component_list(components)

        # Validate circuit
        errors = self._validate_circuit(components, component_list)

        return {
            "components": component_list,
            "nodes": self.nodes,
            "ground_node": self.ground_node,
            "errors": errors,
            "metadata": {
                "num_components": len(component_list),
                "num_nodes": len(self.nodes),
                "has_ground": self.ground_node is not None
            }
        }

    def reset(self):
        """Reset internal state"""
        self.node_counter = 0
        self.node_map = {}
        self.components = []
        self.nodes = {}
        self.ground_node = None

    def _build_connectivity_map(self, components, wires) -> Dict:
        """
        Build a map of which connection points are electrically connected

        Returns dict: connection_point -> set of connected connection_points
        """
        connectivity = {}

        # Each connection point starts in its own group
        for component in components:
            if hasattr(component, 'connection_points'):
                for cp in component.connection_points:
                    connectivity[cp] = {cp}

        # Process wires to merge connection groups
        for wire in wires:
            if hasattr(wire, 'start_point') and hasattr(wire, 'end_point'):
                start = wire.start_point
                end = wire.end_point

                # Ensure both points are in connectivity map
                if start not in connectivity:
                    connectivity[start] = {start}
                if end not in connectivity:
                    connectivity[end] = {end}

                # Merge the two groups
                start_group = connectivity[start]
                end_group = connectivity[end]

                merged_group = start_group | end_group

                # Update all points in merged group to reference the same set
                for point in merged_group:
                    connectivity[point] = merged_group

        return connectivity

    def _assign_node_ids(self, connectivity: Dict):
        """Assign unique node IDs to each connected group"""
        assigned_groups = set()

        for point, connected_group in connectivity.items():
            # Convert set to frozenset for hashing
            group_key = frozenset(connected_group)

            if group_key not in assigned_groups:
                # Assign new node ID
                node_id = f"n{self.node_counter}"
                self.node_counter += 1

                # Map all points in this group to this node
                for p in connected_group:
                    self.node_map[p] = node_id

                # Record this node
                self.nodes[node_id] = list(connected_group)

                assigned_groups.add(group_key)

    def _find_ground_node(self, components):
        """Find the ground node in the circuit"""
        for component in components:
            if hasattr(component, 'component_type') and component.component_type.lower() == 'ground':
                # Ground component's connection point
                if hasattr(component, 'connection_points') and component.connection_points:
                    ground_point = component.connection_points[0]
                    if ground_point in self.node_map:
                        self.ground_node = self.node_map[ground_point]
                        break

    def _build_component_list(self, components) -> List[Dict]:
        """Build list of components with their node connections"""
        component_list = []

        for component in components:
            if not hasattr(component, 'component_type'):
                continue

            comp_type = component.component_type
            comp_name = getattr(component, 'name', comp_type)
            comp_value = getattr(component, 'value', '')

            # Skip ground components (they're just reference)
            if comp_type.lower() == 'ground':
                continue

            # Get nodes this component connects to
            nodes = []
            if hasattr(component, 'connection_points'):
                for cp in component.connection_points:
                    if cp in self.node_map:
                        node_id = self.node_map[cp]
                        nodes.append({
                            "node": node_id,
                            "pin": getattr(cp, 'point_id', 'unknown')
                        })
                    else:
                        # Floating pin
                        nodes.append({
                            "node": None,
                            "pin": getattr(cp, 'point_id', 'unknown')
                        })

            component_list.append({
                "name": comp_name,
                "type": comp_type,
                "value": comp_value,
                "nodes": nodes,
                "position": {
                    "x": component.x(),
                    "y": component.y()
                }
            })

        return component_list

    def _validate_circuit(self, components, component_list) -> List[str]:
        """Validate the circuit and return list of errors/warnings"""
        errors = []

        # Check for ground
        if self.ground_node is None:
            errors.append("WARNING: No ground node found. Circuit may not simulate correctly.")

        # Check for floating nodes
        for comp in component_list:
            for node_info in comp['nodes']:
                if node_info['node'] is None:
                    errors.append(f"ERROR: Component '{comp['name']}' has floating pin '{node_info['pin']}'")

        # Check for components without connections
        for comp in component_list:
            if not comp['nodes'] or all(n['node'] is None for n in comp['nodes']):
                errors.append(f"ERROR: Component '{comp['name']}' is not connected to circuit")

        # Check for missing component values
        for comp in component_list:
            if comp['type'].lower() in ['resistor', 'voltage source', 'current source', 'vdc']:
                if not comp['value'] or comp['value'].strip() == '':
                    errors.append(f"WARNING: Component '{comp['name']}' has no value specified")

        return errors

    def export_spice_netlist(self, netlist: Dict) -> str:
        """
        Export netlist as SPICE format (basic implementation)

        Example output:
        * Circuit netlist
        V1 n1 n0 5V
        R1 n1 n2 1k
        R2 n2 n0 2k
        .end
        """
        lines = ["* SPICE netlist generated by ECis-full", ""]

        ground = netlist.get('ground_node', 'n0')

        for comp in netlist['components']:
            comp_type = comp['type'].lower()
            name = comp['name']
            value = comp['value']
            nodes = comp['nodes']

            if len(nodes) < 2:
                continue

            # Get node names
            node_names = [n['node'] if n['node'] else 'NC' for n in nodes]

            # Convert to SPICE notation
            spice_line = None

            if comp_type == 'resistor':
                # R<name> <node+> <node-> <value>
                spice_line = f"R{name} {node_names[0]} {node_names[1]} {value or '1k'}"

            elif comp_type in ['voltage source', 'vdc']:
                # V<name> <node+> <node-> <value>
                spice_line = f"V{name} {node_names[0]} {node_names[1]} {value or '5V'}"

            elif comp_type == 'current source':
                # I<name> <node+> <node-> <value>
                spice_line = f"I{name} {node_names[0]} {node_names[1]} {value or '1mA'}"

            if spice_line:
                lines.append(spice_line)

        lines.append("")
        lines.append(".end")

        return "\n".join(lines)
