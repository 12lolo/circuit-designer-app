from PyQt6.QtCore import QObject
from components import Wire


class SimulationEngine(QObject):
    """Handles circuit simulation and analysis"""

    def __init__(self, graphics_view):
        super().__init__()
        self.graphics_view = graphics_view

    def simulate_circuit(self, components, wires):
        """Perform basic circuit simulation and return results"""
        try:
            if not components:
                return "No components found in the circuit.\nPlease add components to simulate."

            # Generate circuit grid format
            circuit_grid = self.generate_circuit_grid(components, wires)

            result = "=== CIRCUIT SIMULATION RESULTS ===\n\n"

            # Add the circuit grid dictionary output
            result += "Circuit Grid Format:\n"
            result += "circuit_grid = {\n"

            for key, value in circuit_grid.items():
                result += f"    '{key}': {value},\n"

            result += "}\n\n"

            # Count components by type
            component_counts = {}
            voltage_sources = []
            resistors = []
            current_sources = []
            grounds = []

            for comp in components:
                comp_type = comp.component_type
                component_counts[comp_type] = component_counts.get(comp_type, 0) + 1

                if comp_type in ["Voltage Source", "Vdc"]:
                    voltage_sources.append(comp)
                elif comp_type == "Resistor":
                    resistors.append(comp)
                elif comp_type == "Current Source":
                    current_sources.append(comp)
                elif comp_type == "GND":
                    grounds.append(comp)

            # Display circuit summary
            result += "Circuit Summary:\n"
            for comp_type, count in component_counts.items():
                result += f"  {comp_type}: {count}\n"
            result += f"  Wires: {len(wires)}\n\n"

            # Check for basic circuit validity
            if not grounds:
                result += "⚠️  WARNING: No ground reference found!\n\n"

            if not voltage_sources and not current_sources:
                result += "⚠️  WARNING: No sources found in circuit!\n\n"

            # Simulate basic voltage/current calculations
            result += "Node Analysis:\n"

            if voltage_sources:
                result += f"📊 Voltage Sources ({len(voltage_sources)}):\n"
                for i, vs in enumerate(voltage_sources):
                    voltage = vs.value if vs.value else "0V"
                    result += f"  V{i+1} ({vs.name}): {voltage}\n"
                result += "\n"

            if resistors:
                result += f"🔌 Resistors ({len(resistors)}):\n"
                for i, res in enumerate(resistors):
                    resistance = res.value if res.value else "1kΩ"
                    # Simple current calculation if we have voltage sources
                    if voltage_sources:
                        try:
                            # Extract numeric value from voltage
                            v_val = float(voltage_sources[0].value.replace('V', '').replace('v', '')) if voltage_sources[0].value else 5.0
                            # Extract numeric value from resistance
                            r_str = resistance.replace('Ω', '').replace('Ohm', '').replace('ohm', '')
                            if 'k' in r_str.lower():
                                r_val = float(r_str.replace('k', '').replace('K', '')) * 1000
                            elif 'm' in r_str.lower():
                                r_val = float(r_str.replace('m', '').replace('M', '')) / 1000
                            else:
                                r_val = float(r_str) if r_str else 1000

                            current = v_val / r_val * 1000  # Convert to mA
                            power = v_val * v_val / r_val * 1000  # Convert to mW

                            result += f"  R{i+1} ({res.name}): {resistance}\n"
                            result += f"    Current: {current:.2f} mA\n"
                            result += f"    Power: {power:.2f} mW\n"
                        except:
                            result += f"  R{i+1} ({res.name}): {resistance}\n"
                            result += f"    Current: -- (calculation error)\n"
                    else:
                        result += f"  R{i+1} ({res.name}): {resistance}\n"
                result += "\n"

            if current_sources:
                result += f"⚡ Current Sources ({len(current_sources)}):\n"
                for i, cs in enumerate(current_sources):
                    current = cs.value if cs.value else "1mA"
                    result += f"  I{i+1} ({cs.name}): {current}\n"
                result += "\n"

            # Connection analysis
            result += "Connection Analysis:\n"
            if wires:
                result += f"✅ {len(wires)} wire connections found\n"
            else:
                result += "⚠️  No wire connections found\n"

            # Simple validation checks
            if len(components) >= 2 and len(wires) >= 1 and grounds:
                result += "\n✅ Circuit appears to be properly connected\n"
                result += "🔋 Simulation completed successfully"
            else:
                result += "\n⚠️  Circuit may not be properly connected\n"
                result += "💡 Add components, wires, and ground reference"

            return result

        except Exception as e:
            return f"Simulation Error:\n{str(e)}\n\nPlease check your circuit configuration."

    def generate_circuit_grid(self, components, wires):
        """Generate circuit grid dictionary in the required format"""
        try:
            circuit_grid = {}

            # Sort components for consistent naming
            components_sorted = sorted(components, key=lambda c: (c.component_type, c.pos().x(), c.pos().y()))

            # Track component counters for proper naming
            component_counters = {}
            resistor_counter = 1

            # Process components
            for comp in components_sorted:
                # Convert screen position to grid coordinates
                pos = comp.pos()
                grid_x = int(round(pos.x() / self.graphics_view.grid_spacing))
                grid_y = int(round(pos.y() / self.graphics_view.grid_spacing))

                # Generate component name and type
                comp_type_key = comp.component_type
                if comp_type_key not in component_counters:
                    component_counters[comp_type_key] = 0
                component_counters[comp_type_key] += 1

                if comp.component_type == "GND":
                    if component_counters[comp_type_key] == 1:
                        comp_name = "ground1"
                    else:
                        comp_name = f"ground{component_counters[comp_type_key]}"
                    comp_type = "ground"
                elif comp.component_type in ["Voltage Source", "Vdc"]:
                    if component_counters[comp_type_key] == 1:
                        comp_name = "voltage_source"
                    else:
                        comp_name = f"voltage_source{component_counters[comp_type_key]}"
                    comp_type = "voltage source"
                elif comp.component_type == "Resistor":
                    comp_name = str(resistor_counter)
                    resistor_counter += 1
                    comp_type = "resistor"
                elif comp.component_type == "Current Source":
                    if component_counters[comp_type_key] == 1:
                        comp_name = "current_source1"
                    else:
                        comp_name = f"current_source{component_counters[comp_type_key]}"
                    comp_type = "current source"
                else:
                    comp_name = f"component{component_counters[comp_type_key]}"
                    comp_type = comp.component_type.lower()

                # Get connections - find connected components through wires
                connections = []
                if hasattr(comp, 'connection_points'):
                    connected_coords = set()  # Use set to avoid duplicates

                    for cp in comp.connection_points:
                        if hasattr(cp, 'connected_wires'):
                            for wire in cp.connected_wires:
                                # Get the other end of the wire
                                if hasattr(wire, 'start_point') and hasattr(wire, 'end_point'):
                                    other_point = wire.end_point if wire.start_point == cp else wire.start_point
                                    if hasattr(other_point, 'parentItem') and other_point.parentItem():
                                        other_comp = other_point.parentItem()
                                        other_pos = other_comp.pos()
                                        other_grid_x = int(round(other_pos.x() / self.graphics_view.grid_spacing))
                                        other_grid_y = int(round(other_pos.y() / self.graphics_view.grid_spacing))
                                        connected_coords.add((other_grid_x, other_grid_y))

                    connections = list(connected_coords)

                # Create component entry
                entry = {
                    'coordinate': (grid_x, grid_y),
                    'type': comp_type,
                    'connections': connections
                }

                # Add value if component has one
                if hasattr(comp, 'value') and comp.value:
                    try:
                        # Extract numeric value
                        value_str = comp.value
                        if comp_type == 'voltage source':
                            numeric_value = float(value_str.replace('V', '').replace('v', ''))
                        elif comp_type == 'resistor':
                            if 'k' in value_str.lower():
                                numeric_value = float(value_str.replace('\u03a9', '').replace('k', '').replace('K', '')) * 1000
                            elif 'm' in value_str.lower():
                                numeric_value = float(value_str.replace('\u03a9', '').replace('m', '').replace('M', '')) / 1000
                            else:
                                numeric_value = float(value_str.replace('\u03a9', '').replace('Ohm', '').replace('ohm', ''))
                        elif comp_type == 'current source':
                            if 'm' in value_str.lower():
                                numeric_value = float(value_str.replace('A', '').replace('a', '').replace('m', '').replace('M', '')) / 1000
                            else:
                                numeric_value = float(value_str.replace('A', '').replace('a', ''))
                        else:
                            numeric_value = 0

                        entry['value'] = numeric_value
                    except:
                        # Default values if parsing fails
                        if comp_type == 'voltage source':
                            entry['value'] = 5.0
                        elif comp_type == 'resistor':
                            entry['value'] = 1000.0
                        elif comp_type == 'current source':
                            entry['value'] = 0.001
                else:
                    # Add default values for components without explicit values
                    if comp_type == 'voltage source':
                        entry['value'] = 5.0
                    elif comp_type == 'ground':
                        entry['value'] = 0
                    elif comp_type == 'resistor':
                        entry['value'] = 1000.0

                circuit_grid[comp_name] = entry

            # Process wires - use actual wire positions and connections
            wire_count = 1
            for wire in wires:
                if hasattr(wire, 'start_point') and hasattr(wire, 'end_point'):
                    # Get wire position from actual wire coordinates
                    line = wire.line()
                    wire_x = int(round(line.x1() / self.graphics_view.grid_spacing))
                    wire_y = int(round(line.y1() / self.graphics_view.grid_spacing))

                    # Get actual connections from wire endpoints
                    connections = []

                    # Start point connection
                    if hasattr(wire.start_point, 'parentItem') and wire.start_point.parentItem():
                        start_comp = wire.start_point.parentItem()
                        start_pos = start_comp.pos()
                        start_grid_x = int(round(start_pos.x() / self.graphics_view.grid_spacing))
                        start_grid_y = int(round(start_pos.y() / self.graphics_view.grid_spacing))
                        connections.append((start_grid_x, start_grid_y))

                    # End point connection
                    if hasattr(wire.end_point, 'parentItem') and wire.end_point.parentItem():
                        end_comp = wire.end_point.parentItem()
                        end_pos = end_comp.pos()
                        end_grid_x = int(round(end_pos.x() / self.graphics_view.grid_spacing))
                        end_grid_y = int(round(end_pos.y() / self.graphics_view.grid_spacing))
                        connections.append((end_grid_x, end_grid_y))

                    # Only add wire if it has valid connections
                    if len(connections) == 2:
                        wire_name = f"wire{wire_count}"
                        circuit_grid[wire_name] = {
                            'coordinate': (wire_x, wire_y),
                            'type': 'wire',
                            'connections': connections
                        }
                        wire_count += 1

            return circuit_grid

        except Exception as e:
            return {"error": f"Failed to generate circuit grid: {str(e)}"}
