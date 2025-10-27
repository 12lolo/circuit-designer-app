"""Backend integration module for PySpice simulation"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import QGraphicsScene
from components import Wire, JunctionPoint, ComponentItem
import re

# Try to import PySpice
try:
    from components.core import CircuitGridTransformer, format_output
    PYSPICE_AVAILABLE = True
    PYSPICE_ERROR = None
except ImportError as e:
    PYSPICE_AVAILABLE = False
    PYSPICE_ERROR = str(e)


class BackendSimulator:
    """Integrates the PySpice backend with the circuit designer"""

    def __init__(self):
        self.grid_spacing = 40  # Default grid spacing

    def parse_value(self, value_str: str, component_type: str) -> float:
        """
        Parse component value string to a numerical value

        Args:
            value_str: String like "1kΩ", "5V", "10mA", etc.
            component_type: Type of component

        Returns:
            Float value in base units (Ohms, Volts, Amps)
        """
        if not value_str:
            return 0.0

        # Remove spaces and convert to uppercase for easier parsing
        value_str = value_str.strip().upper()

        # Extract number and unit
        match = re.match(r'([0-9.]+)\s*([A-ZΩ]*)', value_str)
        if not match:
            try:
                return float(value_str)
            except:
                return 0.0

        number_str, unit = match.groups()
        number = float(number_str)

        # Handle metric prefixes
        multipliers = {
            'P': 1e-12,  # pico
            'N': 1e-9,   # nano
            'U': 1e-6,   # micro (µ)
            'M': 1e-3,   # milli
            'K': 1e3,    # kilo
            'MEG': 1e6,  # mega
            'G': 1e9,    # giga
        }

        for prefix, mult in multipliers.items():
            if unit.startswith(prefix):
                return number * mult

        return number

    def scene_to_grid(self, scene: QGraphicsScene, grid_spacing: float = 40) -> Dict:
        """
        Convert PyQt6 scene to circuit_grid format for backend

        Args:
            scene: QGraphicsScene containing the circuit
            grid_spacing: Grid spacing in pixels

        Returns:
            circuit_grid dictionary
        """
        self.grid_spacing = grid_spacing
        circuit_grid = {}

        # Collect all components, wires, and junctions
        components = []
        wires = []
        junctions = []

        for item in scene.items():
            if hasattr(item, 'component_type'):
                components.append(item)
            elif isinstance(item, Wire):
                wires.append(item)
            elif isinstance(item, JunctionPoint):
                junctions.append(item)

        # Add components to grid
        # First pass: create mappings
        # 1. Map connection points to their parent components
        terminal_to_component = {}
        component_positions = {}

        for component in components:
            comp_coord = self._get_grid_coord(component.pos())
            component_positions[component] = comp_coord

            if hasattr(component, 'connection_points'):
                for cp in component.connection_points:
                    terminal_coord = self._get_grid_coord(cp.scenePos())
                    terminal_to_component[terminal_coord] = comp_coord

        # 2. Map wires to their midpoint coordinates
        wire_coords = {}
        for wire in wires:
            if hasattr(wire, 'start_point') and hasattr(wire, 'end_point'):
                start_coord = self._get_grid_coord(wire.start_point.scenePos())
                end_coord = self._get_grid_coord(wire.end_point.scenePos())
                # Wire coordinate is the midpoint (as integer tuple)
                wire_coord = (
                    int(round((start_coord[0] + end_coord[0]) / 2.0)),
                    int(round((start_coord[1] + end_coord[1]) / 2.0))
                )
                wire_coords[wire] = wire_coord

        # Initialize counters for component naming
        name_counters = {}

        # First, find all ground components
        ground_coords = []
        for component in components:
            if component.component_type == 'GND':
                ground_coord = self._get_grid_coord(component.pos())
                ground_coords.append(ground_coord)

        for idx, component in enumerate(components):
            coord = self._get_grid_coord(component.pos())
            component_type = component.component_type

            # Map component types to backend types
            backend_type = self._map_component_type(component_type)

            if backend_type is None:
                continue

            # Find wires that connect to ANY of this component's connection points
            # Components should connect to wire coordinates, not to other component terminals
            connections = []

            if hasattr(component, 'connection_points'):
                for cp in component.connection_points:
                    # For each connection point, find wires connected to it
                    for wire in wires:
                        if not hasattr(wire, 'start_point') or not hasattr(wire, 'end_point'):
                            continue

                        # Check if this wire connects to this connection point (by object identity)
                        is_connected = (wire.start_point is cp) or (wire.end_point is cp)

                        if is_connected and wire in wire_coords:
                            # Connect to the wire's coordinate (midpoint), not to the other end
                            wire_coord = wire_coords[wire]
                            # Ensure wire coordinates are integer tuples
                            wire_coord = (int(round(wire_coord[0])), int(round(wire_coord[1])))
                            if wire_coord not in connections:
                                connections.append(wire_coord)

            # Note: Voltage sources with only 1 connection will be handled in core.py
            # by using circuit.gnd as the second terminal

            # Parse value (convert to int if whole number, otherwise float)
            value = None
            if hasattr(component, 'value') and component.value:
                value = self.parse_value(component.value, component_type)
                # Convert to int if it's a whole number
                if value == int(value):
                    value = int(value)

            # Generate simple component name
            component_name = self._generate_component_name(backend_type, name_counters)

            circuit_grid[component_name] = {
                'coordinate': coord,  # Already integer tuple from _get_grid_coord
                'type': backend_type,
                'connections': connections
            }

            # Add value only for components that need it
            if backend_type in ['resistor', 'voltage_source'] and value is not None:
                circuit_grid[component_name]['value'] = value

        # Get all component coordinates to avoid placing splitwires there
        component_coords = set()
        for comp_name, comp_data in circuit_grid.items():
            if comp_data['type'] != 'wire':  # Only actual components
                component_coords.add(tuple(comp_data['coordinate']) if isinstance(comp_data['coordinate'], list) else comp_data['coordinate'])

        # Add junction points as splitwires (but skip ones at component locations)
        node_counter = 0
        for idx, junction in enumerate(junctions):
            coord = self._get_grid_coord(junction.scenePos())

            # Skip this junction if it's at the same location as a component
            if coord in component_coords:
                continue

            # Find connections as coordinates (tuples), mapped to component coordinates
            connections = self._find_junction_connections(junction, wires, components, junctions, terminal_to_component)
            # Ensure connections are integer tuples
            connections = [(int(round(c[0])), int(round(c[1]))) if isinstance(c, (list, tuple)) else c for c in connections]

            node_counter += 1
            junction_name = f"node{node_counter}"
            circuit_grid[junction_name] = {
                'coordinate': coord,  # already integer tuple from _get_grid_coord
                'type': 'splitwire',
                'connections': connections
            }

        # Add wires with connections mapped to component coordinates
        wire_counter = 0
        for idx, wire in enumerate(wires):
            # Get wire endpoints using actual connection point positions
            start_coord = self._get_grid_coord(wire.start_point.scenePos())
            end_coord = self._get_grid_coord(wire.end_point.scenePos())

            # Map terminal coordinates to component coordinates
            # This is crucial for the CircuitGridTransformer to work correctly
            start_component_coord = terminal_to_component.get(start_coord, start_coord)
            end_component_coord = terminal_to_component.get(end_coord, end_coord)

            # Wire coordinate is the midpoint (from our earlier calculation, already integer)
            wire_coord = wire_coords.get(wire)
            if wire_coord is None:
                # Fallback calculation if not in dict (as integer tuple)
                wire_coord = (
                    int(round((start_coord[0] + end_coord[0]) / 2.0)),
                    int(round((start_coord[1] + end_coord[1]) / 2.0))
                )

            wire_counter += 1
            wire_name = f"wire{wire_counter}"
            circuit_grid[wire_name] = {
                'coordinate': wire_coord,
                'type': 'wire',
                'connections': [start_component_coord, end_component_coord]  # Use component coordinates
            }

        return circuit_grid

    def _get_grid_coord(self, pos) -> tuple:
        """Convert scene position to grid coordinates as integer tuple"""
        x = int(round(pos.x() / self.grid_spacing))
        y = int(round(pos.y() / self.grid_spacing))
        return (x, y)  # Returns integer tuple

    def _map_component_type(self, component_type: str) -> Optional[str]:
        """Map frontend component types to backend types"""
        mapping = {
            'Resistor': 'resistor',
            'Vdc': 'voltage_source',
            'GND': 'ground',
            'Switch': None,  # Not yet implemented in backend
            'Light': None     # Not yet implemented in backend
        }
        return mapping.get(component_type)

    def _generate_component_name(self, component_type: str, counters: dict) -> str:
        """Generate simple component names matching the desired format"""
        if component_type == 'resistor':
            counters['resistor'] = counters.get('resistor', 0) + 1
            return str(counters['resistor'])
        elif component_type == 'voltage_source':
            counters['voltage_source'] = counters.get('voltage_source', 0) + 1
            if counters['voltage_source'] == 1:
                return 'voltage_source'
            return f'voltage_source{counters["voltage_source"]}'
        elif component_type == 'ground':
            counters['ground'] = counters.get('ground', 0) + 1
            return f'ground{counters["ground"]}'
        return f'{component_type}_{counters.get(component_type, 0)}'

    def _find_wire_connections(self, connection_point, wires, components, junctions) -> List[tuple]:
        """Find all coordinates connected to a connection point via wires"""
        connections = []

        for wire in wires:
            if not (hasattr(wire, 'start_point') and hasattr(wire, 'end_point')):
                continue

            other_point = None

            # Check if this wire connects to our connection point (by object identity)
            if wire.start_point is connection_point:
                other_point = wire.end_point
            elif wire.end_point is connection_point:
                other_point = wire.start_point

            if other_point:
                # Get the coordinate of the other end
                other_coord = self._get_grid_coord(other_point.scenePos())
                connections.append(other_coord)

        return connections

    def _find_junction_connections(self, junction, wires, components, junctions, terminal_to_component) -> List[tuple]:
        """Find all coordinates connected to a junction, mapped to component coordinates"""
        connections = []

        for wire in wires:
            if not (hasattr(wire, 'start_point') and hasattr(wire, 'end_point')):
                continue

            other_point = None

            # Check if wire connects to this junction (by object identity)
            if wire.start_point is junction:
                other_point = wire.end_point
            elif wire.end_point is junction:
                other_point = wire.start_point

            if other_point:
                # Get the coordinate of the other end using actual position
                other_coord = self._get_grid_coord(other_point.scenePos())
                # Map to component coordinate if it's a terminal
                component_coord = terminal_to_component.get(other_coord, other_coord)
                connections.append(component_coord)

        return connections

    def _validate_circuit(self, circuit_grid: Dict) -> Dict:
        """Validate circuit before simulation"""
        errors = []

        # Check if there's at least one voltage source
        has_voltage_source = False
        has_ground = False

        for name, data in circuit_grid.items():
            if data['type'] == 'voltage_source':
                has_voltage_source = True
                # Check if voltage source has a value
                if data.get('value', 0) == 0:
                    errors.append(f"Voltage source '{name}' has no value set")
            elif data['type'] == 'ground':
                has_ground = True
            elif data['type'] == 'resistor':
                # Check if resistor has a value
                if data.get('value', 0) <= 0:
                    errors.append(f"Resistor '{name}' has invalid value: {data.get('value', 0)}")

        if not has_voltage_source:
            return {
                'valid': False,
                'error': 'Circuit must have at least one voltage source',
                'details': 'Add a voltage source (Vdc) to your circuit'
            }

        if not has_ground:
            return {
                'valid': False,
                'error': 'Circuit must have at least one ground connection',
                'details': 'Add a GND component to your circuit'
            }

        if errors:
            return {
                'valid': False,
                'error': 'Circuit has invalid component values',
                'details': '\n'.join(errors)
            }

        return {'valid': True}

    def run_simulation(self, scene: QGraphicsScene, grid_spacing: float = 40) -> Dict:
        """
        Run PySpice simulation on the circuit

        Args:
            scene: QGraphicsScene containing the circuit
            grid_spacing: Grid spacing in pixels

        Returns:
            Dictionary with simulation results or errors
        """
        # Check if PySpice is available
        if not PYSPICE_AVAILABLE:
            return {
                'success': False,
                'error': 'PySpice is not installed or could not be imported',
                'error_type': 'ImportError',
                'details': PYSPICE_ERROR or 'PySpice module not found',
                'install_command': 'pip install PySpice'
            }

        try:
            # Convert scene to circuit grid
            circuit_grid = self.scene_to_grid(scene, grid_spacing)

            if not circuit_grid:
                return {
                    'success': False,
                    'error': 'No components found in circuit'
                }

            # Validate circuit before simulation
            validation = self._validate_circuit(circuit_grid)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error'],
                    'error_type': 'ValidationError',
                    'details': validation.get('details', '')
                }

            # Make a deep copy for debugging before transformation
            import copy
            original_grid_copy = copy.deepcopy(circuit_grid)

            # Transform grid (remove wires, restructure)
            # NOTE: This modifies circuit_grid in place!
            transformer = CircuitGridTransformer(circuit_grid)
            transformer.remove_wires_and_restructure()

            # Debug: store both original and transformed grid
            debug_info = {
                'original_grid': original_grid_copy,
                'transformed_grid': copy.deepcopy(transformer.circuit_grid)
            }

            # Convert to PySpice circuit
            pyspice_circuit = transformer.grid_to_pyspice_circuit()

            # Get the netlist for debugging
            netlist_str = str(pyspice_circuit)

            # Run simulation
            simulator = pyspice_circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.operating_point()

            # Format results
            results = format_output(analysis)

            return {
                'success': True,
                'results': results,
                'circuit_grid': transformer.circuit_grid,
                'netlist': netlist_str,
                'debug_info': debug_info
            }

        except Exception as e:
            import traceback
            import json

            # Try to include debug info even on failure
            debug_data = {}
            try:
                # Use the original_grid_copy if it exists, otherwise use circuit_grid
                if 'original_grid_copy' in locals():
                    debug_data['original_grid'] = json.dumps(original_grid_copy, indent=2, default=str)
                elif 'circuit_grid' in locals():
                    debug_data['original_grid'] = json.dumps(circuit_grid, indent=2, default=str)

                if 'debug_info' in locals() and 'transformed_grid' in debug_info:
                    debug_data['transformed_grid'] = json.dumps(debug_info['transformed_grid'], indent=2, default=str)
                elif 'transformer' in locals():
                    debug_data['transformed_grid'] = json.dumps(transformer.circuit_grid, indent=2, default=str)

                if 'pyspice_circuit' in locals():
                    debug_data['netlist'] = str(pyspice_circuit)
            except:
                pass

            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'debug_data': debug_data
            }
