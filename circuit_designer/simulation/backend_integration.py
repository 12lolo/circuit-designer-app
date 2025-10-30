"""Backend integration module for PySpice simulation"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import QGraphicsScene
from circuit_designer.components import Wire, ComponentItem
import re

# Try to import PySpice
try:
    from circuit_designer.components.core import CircuitGridTransformer, format_output
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
            value_str: String like "1kΩ", "5V", "10mA", "Open", "Closed", etc.
            component_type: Type of component

        Returns:
            Float value in base units (Ohms, Volts, Amps)
            For switches: 1e9 (very high) for Open, 0.001 for Closed
        """
        if not value_str:
            return 0.0

        # Handle switch states specially
        value_str_stripped = value_str.strip()
        if value_str_stripped == "Open":
            return 1e9  # Very high resistance for open switch (essentially infinite)
        elif value_str_stripped == "Closed":
            return 0.001  # Very low resistance for closed switch (essentially zero)
        elif value_str_stripped == "Off":
            # LED "Off" state - use default LED resistance
            return 100.0  # 100 ohms default for LED

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

    def scene_to_grid(self, scene: QGraphicsScene, grid_spacing: float = 40) -> tuple:
        """
        Convert PyQt6 scene to circuit_grid format for backend

        Args:
            scene: QGraphicsScene containing the circuit
            grid_spacing: Grid spacing in pixels

        Returns:
            Tuple of (circuit_grid dictionary, component_name_mapping dictionary)
        """
        self.grid_spacing = grid_spacing
        circuit_grid = {}

        # Collect all components and wires
        components = []
        wires = []

        for item in scene.items():
            if hasattr(item, 'component_type'):
                components.append(item)
            elif isinstance(item, Wire):
                wires.append(item)

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

        # Store mapping from backend component name to scene component object
        component_name_mapping = {}

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
                print(f"DEBUG: Component {backend_type} at {coord} - raw value: '{component.value}'")
                value = self.parse_value(component.value, component_type)
                print(f"DEBUG: Component {backend_type} at {coord} - parsed value: {value}")
                # Convert to int if it's a whole number
                if value == int(value):
                    value = int(value)
            else:
                print(f"DEBUG: Component {backend_type} at {coord} - NO VALUE")

            # Generate simple component name
            component_name = self._generate_component_name(backend_type, name_counters)

            # Store mapping from backend name to scene component
            component_name_mapping[component_name] = component

            circuit_grid[component_name] = {
                'coordinate': coord,  # Already integer tuple from _get_grid_coord
                'type': backend_type,
                'connections': connections
            }

            # Add value only for components that need it, with defaults for missing values
            if backend_type in ['resistor', 'voltage_source', 'switch', 'led']:
                if value is not None:
                    circuit_grid[component_name]['value'] = value
                else:
                    # Set reasonable defaults for components without values
                    if backend_type == 'resistor':
                        circuit_grid[component_name]['value'] = 1000  # 1kΩ default
                        print(f"DEBUG: Resistor '{component_name}' - using default 1kΩ")
                    elif backend_type == 'voltage_source':
                        circuit_grid[component_name]['value'] = 5  # 5V default
                        print(f"DEBUG: Voltage source '{component_name}' - using default 5V")
                    elif backend_type == 'switch':
                        circuit_grid[component_name]['value'] = 0.001  # Closed by default
                        print(f"DEBUG: Switch '{component_name}' - using default Closed (0.001Ω)")
                    elif backend_type == 'led':
                        circuit_grid[component_name]['value'] = 100  # 100Ω default
                        print(f"DEBUG: LED '{component_name}' - using default 100Ω")

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

        return circuit_grid, component_name_mapping

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
            'Switch': 'switch',
            'LED': 'led'
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
        elif component_type == 'switch':
            counters['switch'] = counters.get('switch', 0) + 1
            return f'switch{counters["switch"]}'
        elif component_type == 'led':
            counters['led'] = counters.get('led', 0) + 1
            return f'led{counters["led"]}'
        return f'{component_type}_{counters.get(component_type, 0)}'


    def _validate_circuit(self, circuit_grid: Dict) -> Dict:
        """Validate circuit before simulation"""
        errors = []
        warnings = []

        # Check if there's at least one voltage source
        has_voltage_source = False
        has_ground = False
        disconnected_components = []

        for name, data in circuit_grid.items():
            comp_type = data['type']
            connections = data.get('connections', [])

            if comp_type == 'voltage_source':
                has_voltage_source = True
                # Check if voltage source has a value
                if data.get('value', 0) == 0:
                    errors.append(f"Voltage source '{name}' has no value set")
                # Check if voltage source has proper connections
                if len(connections) < 1:
                    errors.append(f"Voltage source '{name}' is not connected to any components")
                    disconnected_components.append(name)
                elif len(connections) < 2:
                    warnings.append(f"Voltage source '{name}' may not have enough connections (needs 2 terminals)")

            elif comp_type == 'ground':
                has_ground = True
                # Ground should have at least one connection
                if len(connections) < 1:
                    errors.append(f"Ground '{name}' is not connected to any components")
                    disconnected_components.append(name)

            elif comp_type == 'resistor':
                # Check if resistor has a value
                if data.get('value', 0) <= 0:
                    errors.append(f"Resistor '{name}' has invalid value: {data.get('value', 0)}")
                # Check if resistor has connections
                if len(connections) < 1:
                    errors.append(f"Resistor '{name}' is not connected to any components")
                    disconnected_components.append(name)
                elif len(connections) < 2:
                    warnings.append(f"Resistor '{name}' may not have enough connections (needs 2 terminals)")

            elif comp_type == 'led':
                # Check if LED has connections
                if len(connections) < 1:
                    errors.append(f"LED '{name}' is not connected to any components")
                    disconnected_components.append(name)
                elif len(connections) < 2:
                    warnings.append(f"LED '{name}' may not have enough connections (needs 2 terminals)")

            elif comp_type == 'switch':
                # Check if switch has connections
                if len(connections) < 1:
                    errors.append(f"Switch '{name}' is not connected to any components")
                    disconnected_components.append(name)
                elif len(connections) < 2:
                    warnings.append(f"Switch '{name}' may not have enough connections (needs 2 terminals)")

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

        if disconnected_components:
            return {
                'valid': False,
                'error': f'Circuit has {len(disconnected_components)} disconnected component(s)',
                'details': f'The following components are not connected:\n' + '\n'.join(f'  • {name}' for name in disconnected_components) + '\n\nConnect all components with wires before simulating.'
            }

        if errors:
            return {
                'valid': False,
                'error': 'Circuit has validation errors',
                'details': '\n'.join(errors)
            }

        # Warnings don't prevent simulation, but we could log them
        if warnings:
            # Could log these, but don't fail validation
            pass

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
            circuit_grid, component_name_mapping = self.scene_to_grid(scene, grid_spacing)

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
                'debug_info': debug_info,
                'component_name_mapping': component_name_mapping
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
