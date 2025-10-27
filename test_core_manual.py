#!/usr/bin/env python3
"""
Manual test of core.py with a simple circuit:
20V voltage source → 1Ω resistor → Ground

Expected output:
- Current: I = V/R = 20V / 1Ω = 20A
- Node voltage between source and resistor: 20V
- Node voltage at ground: 0V
"""

import sys
sys.path.insert(0, '/home/senne/PycharmProjects/circuit-designer-app')

from components.core import CircuitGridTransformer, format_output

# Create a simple circuit grid matching the desired format
# Voltage source has ONE connection (core.py will use ground as second terminal)
circuit_grid = {
    'voltage_source': {
        'coordinate': (0, 0),
        'type': 'voltage_source',
        'connections': [(0, -1)],  # Connects to wire1 only
        'value': 20
    },
    'wire1': {
        'coordinate': (0, -1),
        'type': 'wire',
        'connections': [(0, 0), (0, -2)]  # Connects voltage_source to resistor
    },
    '1': {
        'coordinate': (0, -2),
        'type': 'resistor',
        'connections': [(0, -1), (0, -3)],  # Connects to wire1 and wire2
        'value': 1
    },
    'wire2': {
        'coordinate': (0, -3),
        'type': 'wire',
        'connections': [(0, -2), (0, -4)]  # Connects resistor to ground
    },
    'ground1': {
        'coordinate': (0, -4),
        'type': 'ground',
        'connections': [(0, -3)]  # Connects to wire2
    }
}

print("=" * 60)
print("MANUAL TEST: 20V → 1Ω → Ground")
print("=" * 60)
print("\nOriginal Circuit Grid:")
for name, data in circuit_grid.items():
    print(f"  {name}: {data}")

# Transform the circuit (remove wires and connect components directly)
print("\n" + "=" * 60)
print("Running CircuitGridTransformer...")
print("=" * 60)

transformer = CircuitGridTransformer(circuit_grid)
transformer.remove_wires_and_restructure()

print("\nTransformed Circuit Grid (after wire removal):")
for name, data in transformer.circuit_grid.items():
    print(f"  {name}: {data}")

# Convert to PySpice circuit
print("\n" + "=" * 60)
print("Generating PySpice Netlist...")
print("=" * 60)

try:
    pyspice_circuit = transformer.grid_to_pyspice_circuit()
    netlist = str(pyspice_circuit)
    print("\nGenerated Netlist:")
    print(netlist)

    # Run simulation
    print("\n" + "=" * 60)
    print("Running Simulation...")
    print("=" * 60)

    simulator = pyspice_circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.operating_point()

    # Format and display results
    results = format_output(analysis)

    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    print("\nNode Voltages:")
    for node_name, voltage in results.items():
        print(f"  {node_name}: {voltage[0]:.6f} V")

    print("\n" + "=" * 60)
    print("EXPECTED vs ACTUAL")
    print("=" * 60)
    print("\nExpected:")
    print("  - Node between voltage_source and resistor: ~20.0 V")
    print("  - Node between resistor and ground: ~0.0 V")
    print("  - Current through circuit: 20 A")

    print("\nActual:")
    if len(results) == 0:
        print("  ❌ NO NODE VOLTAGES FOUND!")
    elif len(results) == 1:
        print(f"  ⚠️  ONLY ONE NODE FOUND: {list(results.keys())[0]} = {list(results.values())[0][0]:.6f} V")
        print("  ❌ Missing ground or voltage source connection!")
    else:
        print(f"  ✓ Found {len(results)} nodes")
        for node_name, voltage in results.items():
            print(f"    {node_name}: {voltage[0]:.6f} V")

except Exception as e:
    import traceback
    print("\n" + "=" * 60)
    print("ERROR OCCURRED")
    print("=" * 60)
    print(f"\nError: {e}")
    print("\nFull traceback:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
