"""
Core simulation engine for electronic circuit analysis.

This module serves as the central component of the circuit simulator package,
handling simulation execution and result processing.
"""


import numpy as np

import PySpice
from PySpice.Logging import Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *


logger = Logging.setup_logging()


class CircuitGridTransformer:
    """Transforms a grid-based circuit representation into a simplified PySpice-compatible structure."""
    def __init__(self, circuit_grid):
        """Initialize the transformer with a circuit grid.
        
        Args:
            circuit_grid: The grid that will be simplified to connect all components directly instead of with wires."""
        self.circuit_grid = circuit_grid

    def _get_component_connections(self, component_name):
        """
        Get valid connections for a component by filtering out non-existent coordinates.
        
        Args:
            component_name: Name of the component to check connections for.
        
        Returns:
            List of valid coordinate connections that exist in the circuit grid.
        """
        component_data = self.circuit_grid[component_name]
        connections = []

        for connection in component_data['connections']:
            for _, refference_component_data in self.circuit_grid.items():
                if connection != refference_component_data['coordinate']:
                    continue

                if component_data['coordinate'] not in refference_component_data['connections']:
                    continue

                connections.append(connection)

        return connections

    def remove_wires_and_restructure(self):
        """
        Remove wire components and directly connect the components they were connecting.

        Returns:
            Simplified circuit circuit grid without wire components
        """
        # Normalize all coordinates to tuples for consistent comparison
        for name, data in self.circuit_grid.items():
            if isinstance(data['coordinate'], list):
                data['coordinate'] = tuple(data['coordinate'])
            data['connections'] = [tuple(c) if isinstance(c, list) else c for c in data['connections']]

        # First pass: replace all wire coordinates in component connections with component coordinates
        for wire_name, wire_data in list(self.circuit_grid.items()):
            if wire_data['type'] != 'wire':
                continue

            wire_coordinate = tuple(wire_data['coordinate']) if isinstance(wire_data['coordinate'], list) else wire_data['coordinate']
            wire_connections = [tuple(c) if isinstance(c, list) else c for c in wire_data['connections']]

            # Update all components that connect to this wire
            for component_name, component_data in self.circuit_grid.items():
                if component_data['type'] == 'wire':
                    continue

                comp_coord = tuple(component_data['coordinate']) if isinstance(component_data['coordinate'], list) else component_data['coordinate']

                # Check if this component connects to this wire
                if wire_coordinate not in component_data['connections']:
                    continue

                # Find the other components this wire connects to (excluding this component)
                other_components = [coord for coord in wire_connections if coord != comp_coord]

                # Replace the wire coordinate with direct connections to other components
                new_connections = []
                for conn in component_data['connections']:
                    conn = tuple(conn) if isinstance(conn, list) else conn
                    if conn == wire_coordinate:
                        # Replace wire connection with connections to other components
                        new_connections.extend(other_components)
                    else:
                        new_connections.append(conn)

                component_data['connections'] = new_connections

        # Second pass: remove wires from circuit grid
        self.circuit_grid = {name: data for name, data in self.circuit_grid.items() if data['type'] != 'wire'}

        # Third pass: ensure bidirectional connections (if A connects to B, B must connect to A)
        for component_name, component_data in self.circuit_grid.items():
            comp_coord = tuple(component_data['coordinate']) if isinstance(component_data['coordinate'], list) else component_data['coordinate']
            for connection_coord in component_data['connections']:
                connection_coord = tuple(connection_coord) if isinstance(connection_coord, list) else connection_coord
                # Find the component at connection_coord
                for other_name, other_data in self.circuit_grid.items():
                    other_coord = tuple(other_data['coordinate']) if isinstance(other_data['coordinate'], list) else other_data['coordinate']
                    if other_coord == connection_coord:
                        # Ensure bidirectional connection
                        if comp_coord not in other_data['connections']:
                            other_data['connections'].append(comp_coord)
                        break

        # Fourth pass: validate mutual connections and remove duplicates
        for component_name, component_data in self.circuit_grid.items():
            valid_connections = self._get_component_connections(component_name)
            # Remove duplicates while preserving order
            component_data['connections'] = list(dict.fromkeys(valid_connections))

        self._name_connections()

    def _name_connections(self):
        """Replace the connection coordinates with the names of the components."""
        coordinate_to_name = {data['coordinate']: name for name, data in self.circuit_grid.items()}

        for component_name, component_data in self.circuit_grid.items():
            connections_by_name = []

            for connection_coordinate in component_data['connections']:
                # Ensure coordinate is a tuple
                if isinstance(connection_coordinate, list):
                    connection_coordinate = tuple(connection_coordinate)

                # Check if coordinate exists in mapping
                if connection_coordinate not in coordinate_to_name:
                    print(f"WARNING: Component '{component_name}' at {component_data['coordinate']} has connection to {connection_coordinate} which doesn't exist in circuit")
                    print(f"Available coordinates: {list(coordinate_to_name.keys())}")
                    continue  # Skip invalid connection

                connections_by_name.append(coordinate_to_name[connection_coordinate])
            component_data['connections'] = connections_by_name

    def grid_to_pyspice_circuit(self, circuit_name = 'GridCircuit'):
        """
        Convert a simplified circuit grid to a PySpice Circuit object.
        
        Args:
            circuit_name: Name for the PySpice circuit.
        
        Returns:
            PySpice Circuit object with all input components connected.
        """
        circuit = Circuit(circuit_name)
        supporting_resistors = 0

        for component_name, component_data in self.circuit_grid.items():

            match component_data['type']:
                case 'voltage_source':
                    component_function = circuit.V
                    unit = component_data['value']@u_V
                case 'resistor' | 'switch' | 'led':
                    # Resistors, switches (as variable resistors), and LEDs (as resistors)
                    component_function = circuit.R
                    unit = component_data['value']@u_Ohm
                case 'splitwire':
                    for connection in component_data['connections']:
                        if self.circuit_grid[connection]['type'] != 'ground':
                            continue
                        circuit.R(f'supporting_resistor{supporting_resistors}', component_name, circuit.gnd, 0.001@u_Ohm)
                        supporting_resistors += 1  # Increment counter to avoid duplicate names
                    continue
                case _:
                    continue

            # Special handling for voltage sources with only 1 connection
            if component_data['type'] == 'voltage_source' and len(component_data['connections']) == 1:
                # Use the single connection as positive terminal and ground as negative
                positive_node = self._create_single_node_name(component_name, component_data['connections'][0], circuit)
                negative_node = circuit.gnd

                component_function(
                    component_name,
                    positive_node,
                    negative_node,
                    unit
                )
                continue

            if len(component_data['connections']) != 2:
                continue

            node_names = self._create_node_names(component_name, component_data, circuit)

            component_function(
                component_name,
                node_names['positive'],
                node_names['negative'],
                unit
            )

        return circuit

    def _create_single_node_name(self, component_name, connection, circuit):
        """
        Generate a single node name for a component with only one connection.

        Args:
            component_name: Name of the component
            connection: Single connection name
            circuit: PySpice Circuit object

        Returns:
            Node name string or circuit.gnd
        """
        connected_component = self.circuit_grid[connection]

        if connected_component['type'] == 'ground':
            return circuit.gnd
        elif connected_component['type'] == 'splitwire':
            return connection
        else:
            node_components = sorted([component_name, connection])
            return f'{node_components[0]}/{node_components[1]}'

    def _create_node_names(self, component_name, component_data, circuit):
        """
        Generate node names for component connections in PySpice circuit.

        Args:
            component_name: Name of the component
            component_data: Component data with 'connections' and 'type'
            circuit: PySpice Circuit object

        Returns:
            dict: {'positive': node_name, 'negative': node_name} for connections
        """
        connection = 0
        node_names = {'positive': None, 'negative': None}

        for node in node_names:
            node_components = sorted([component_name, component_data['connections'][connection]])
            match self.circuit_grid[component_data['connections'][connection]]['type']:
                case 'ground':
                    node_names[node] = circuit.gnd
                case 'splitwire':
                    node_names[node] = component_data['connections'][connection]
                case _:
                    node_names[node] = f'{node_components[0]}/{node_components[1]}'

            connection += 1

        return node_names


def format_output(analysis):
    """Format the output results of the simulation in a dictionary."""
    simulation_results_dict = {}

    for node_name, node_value in analysis.nodes.items():
        data_label = str(node_name)
        # Convert the node value to a numpy array with proper value extraction
        # PySpice returns node values that can be directly converted to float
        try:
            # For operating point analysis, node_value is already the voltage value
            voltage_value = float(node_value)
            simulation_results_dict[data_label] = np.array([voltage_value])
        except (TypeError, ValueError):
            # Fallback: try to extract from array-like object
            simulation_results_dict[data_label] = np.array([float(node_value[0])]) if hasattr(node_value, '__getitem__') else np.array([0.0])

    return simulation_results_dict


def main():
    """Main function to run the test circuit simulation."""
    circuit_grid = {
        'voltage_source':
        {'coordinate': (0, 0), 'type': 'voltage_source', 'connections': [(1, 0), (-1, 0)], 'value': 20},
        'ground1': {'coordinate': (-1, 0), 'type': 'ground', 'connections': [(0, 0)]},
        'wire1': {'coordinate': (1, 0), 'type': 'wire', 'connections': [(0, 0), (1, -1)]},
        '1': {'coordinate': (1, -1), 'type': 'resistor', 'connections': [(1, 0), (1, -2)], 'value': 10},
        'wire2': {'coordinate': (1, -2), 'type': 'wire', 'connections': [(1, -1), (10, 10)]},
        'wire10': {'coordinate': (10, 10), 'type': 'wire', 'connections': [(1, -2), (11, 11)]},
        'wire11': {'coordinate': (11, 11), 'type': 'wire', 'connections': [(10, 10), (0, -2)]},
        'node1': {'coordinate': (0, -2), 'type': 'splitwire', 'connections': [(11, 11), (0, -1), (0, -3)]},
        'wire4': {'coordinate': (0, -1), 'type': 'wire', 'connections': [(0, -2), (-1, -1)]},
        '2': {'coordinate': (-1, -1), 'type': 'resistor', 'connections': [(0, -1), (-2, -1)], 'value': 20},
        'wire5': {'coordinate': (-2, -1), 'type': 'wire', 'connections': [(-1, -1), (-2, -2)]},
        'node2': {'coordinate': (-2, -2), 'type': 'splitwire', 'connections': [(-2, -1), (-3, -2), (-2, -3)]},
        'wire7': {'coordinate': (0, -3), 'type': 'wire', 'connections': [(0, -2), (-1, -3)]},
        '3': {'coordinate': (-1, -3), 'type': 'resistor', 'connections': [(0, -3), (-2, -3)], 'value': 30},
        'wire8': {'coordinate': (-2, -3), 'type': 'wire', 'connections': [(-1, -3), (-2, -2)]},
        'ground2': {'coordinate': (-3, -2), 'type': 'ground', 'connections': [(-2, -2)]}
    }

    transformer = CircuitGridTransformer(circuit_grid)

    transformer.remove_wires_and_restructure()

    pyspice_circuit = transformer.grid_to_pyspice_circuit()

    simulator = pyspice_circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.operating_point()

    print(format_output(analysis))


if __name__ == "__main__":
    main()
