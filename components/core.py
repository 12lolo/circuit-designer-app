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
        for wire_name, wire_data in self.circuit_grid.items():
            if wire_data['type'] != 'wire':
                continue

            wire_connections = self._get_component_connections(wire_name)

            if len(wire_connections) < 2:
                continue

            # Update components connected to this wire
            for _, component_data in self.circuit_grid.items():
                if component_data['coordinate'] not in wire_connections:
                    continue

                # Replace wire connection with direct connection to other end
                for coordinate in wire_connections:
                    if coordinate != component_data['coordinate']:
                        wire_coordinate_index = component_data['connections'].index(wire_data['coordinate'])
                        component_data['connections'][wire_coordinate_index] = coordinate

        self.circuit_grid = {name: data for name, data in self.circuit_grid.items() if data['type'] != 'wire'}

        # Remove all invalid connections
        for component_name, component_data in self.circuit_grid.items():
            valid_connections = self._get_component_connections(component_name)
            component_data['connections'] = valid_connections

        self._name_connections()

    def _name_connections(self):
        """Replace the connection coordinates with the names of the components."""
        coordinate_to_name = {data['coordinate']: name for name, data in self.circuit_grid.items()}

        for _, component_data in self.circuit_grid.items():
            connections_by_name = []

            for connection_coordinate in component_data['connections']:
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
                case 'resistor':
                    component_function = circuit.R
                    unit = component_data['value']@u_Ohm
                case 'splitwire':
                    for connection in component_data['connections']:
                        if self.circuit_grid[connection]['type'] != 'ground':
                            continue
                        circuit.R(f'supporting_resistor{supporting_resistors}', component_name, circuit.gnd, 0@u_Ohm)
                    continue
                case _:
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

    for node in analysis.nodes.values():
        data_label = f"{node}"
        simulation_results_dict[data_label] = np.array(node)

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
