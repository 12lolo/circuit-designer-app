# Circuit Designer

A professional PyQt6-based electronic circuit design and simulation application with PySpice integration.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

## Overview

Circuit Designer is a modern, intuitive circuit design and simulation tool that combines visual circuit creation with powerful SPICE-based simulation capabilities. Build, analyze, and understand electronic circuits with an easy-to-use drag-and-drop interface.

## Features

### Core Functionality
- 🎨 **Visual Circuit Design** - Intuitive drag-and-drop component placement
- ⚡ **Real-Time Simulation** - Powered by PySpice and ngspice
- 💾 **Project Management** - Save, load, and organize your circuit designs
- 🔧 **Component Library** - Resistors, voltage sources, LEDs, switches, and ground components
- ↩️ **Undo/Redo** - Complete undo/redo support for all operations
- 📊 **Simulation Results** - Detailed node voltage analysis and circuit diagnostics

### Advanced Features
- **Wire Routing** - Smart wire connections with bend point support
- **Component Rotation** - Rotate components to any orientation (0°, 90°, 180°, 270°)
- **Grid Snapping** - Automatic alignment for professional-looking circuits
- **LED Indicators** - Visual feedback showing LED state based on voltage thresholds
- **Copy/Paste** - Duplicate circuit sections quickly
- **Export** - Save circuit diagrams as PNG images

### User Experience
- ⌨️ **Keyboard Shortcuts** - Streamlined workflow for power users
- 🖱️ **Context Menus** - Right-click actions for quick access
- 📋 **Component Inspector** - Edit component properties in real-time
- 📝 **Activity Log** - Track all operations and simulation results
- 🎯 **Zoom & Pan** - Navigate large circuit designs easily

## Installation

### Prerequisites

**System Requirements:**
- Python 3.8 or higher
- ngspice (circuit simulation engine)

**Install ngspice:**

```bash
# Arch Linux
sudo pacman -S ngspice

# Ubuntu/Debian
sudo apt install ngspice

# Fedora/RHEL
sudo dnf install ngspice

# macOS
brew install ngspice

# Windows (via Scoop)
scoop install ngspice
```

### Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

**Main dependencies:**
- PyQt6 - GUI framework
- PySpice - SPICE simulation interface
- NumPy - Numerical operations

## Quick Start

### Running the Application

**Option 1: Python script**
```bash
python3 app.py
```

**Option 2: Shell script (Linux/macOS)**
```bash
chmod +x run.sh
./run.sh
```

### Creating Your First Circuit

1. **Add Components**
   - Drag components from the left panel onto the canvas
   - Available: Resistor, Voltage Source (Vdc), LED, Switch, Ground

2. **Connect Components**
   - Click on a connection point (colored dot) on one component
   - Click on a connection point on another component
   - A wire will be created between them

3. **Set Component Values**
   - Select a component by clicking it
   - Use the Inspect Panel (right side) to set values
   - Example: Set resistor to "1k" or "1000"

4. **Add Ground**
   - Every circuit must have at least one ground component
   - Drag the Ground component onto the canvas

5. **Run Simulation**
   - Press `F5` or click "Run Simulation" button
   - View results in the Simulation Output panel (bottom right)

### Adding Wire Bend Points

- Right-click on any wire to add a bend point
- Drag bend points to route wires around components
- Create professional-looking circuit layouts

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **File Operations** |
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |
| **Editing** |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `Ctrl+C` | Copy selected components |
| `Ctrl+V` | Paste components |
| `Delete` | Delete selected items |
| **Component Operations** |
| `R` | Rotate selected component |
| **View** |
| `Ctrl+=` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| **Simulation** |
| `F5` | Run simulation |
| **Selection** |
| `Ctrl+A` | Select all |
| `Escape` | Deselect all |

## Project Structure

```
circuit-designer-app/
├── app.py                          # Application entry point
├── run.sh                          # Launch script
├── requirements.txt                # Python dependencies
├── circuit_designer/               # Main application package
│   ├── core/                       # Core application logic
│   │   ├── main_window.py          # Main window coordinator
│   │   └── managers/               # Specialized managers
│   │       ├── canvas_manager.py   # Viewport and grid operations
│   │       ├── component_manager.py # Component placement and properties
│   │       ├── wire_manager.py     # Wire creation and validation
│   │       └── selection_manager.py # Selection and clipboard
│   ├── components/                 # Circuit components
│   │   ├── component_item.py       # Base component class
│   │   ├── connection_points.py    # Connection and bend points
│   │   ├── wire.py                 # Wire with routing support
│   │   └── graphics_view.py        # Custom graphics view
│   ├── simulation/                 # Simulation engine
│   │   ├── backend_integration.py  # PySpice interface
│   │   ├── netlist_builder.py      # Circuit netlist generation
│   │   └── simulation_engine.py    # Simulation coordinator
│   ├── ui/                         # User interface components
│   │   ├── panels/                 # UI panels
│   │   ├── dialogs/                # Dialog windows
│   │   ├── widgets/                # Custom widgets
│   │   └── managers/               # UI managers
│   ├── project/                    # Project management
│   │   ├── project_manager.py      # Save/load operations
│   │   └── undo_commands.py        # Undo/redo system
│   └── utils/                      # Utilities
│       ├── spatial_grid.py         # Grid and collision detection
│       └── canvas_tools.py         # Canvas utilities
├── projects/                       # Saved project files (.ecis)
└── tests/                          # Test suite
```

## Architecture

Circuit Designer follows a modular architecture with clear separation of concerns:

- **Core Layer** - Application coordination and window management
- **Components Layer** - Visual circuit elements and behavior
- **Simulation Layer** - SPICE integration and analysis
- **UI Layer** - User interface panels and widgets
- **Project Layer** - Persistence and undo/redo
- **Utils Layer** - Shared utilities and helpers

## File Format

Projects are saved as `.ecis` (Electronic Circuit Simulator) files containing:
- Circuit components with positions and properties
- Wire connections and routing information
- Thumbnail preview image

Files are stored in JSON format for easy inspection and version control.

## Component Details

### Resistor
- Configurable resistance value (supports k, M suffixes)
- Example values: "1k", "4.7k", "1M", "100"
- Default: 1kΩ

### Voltage Source (Vdc)
- DC voltage source
- Configurable voltage value
- Default: 5V

### LED
- Visual indicator with voltage threshold
- Configurable threshold voltage
- Shows ON/OFF state after simulation
- Default threshold: 1.5V

### Switch
- Open/Closed states
- Simulated as very high/low resistance
- Toggle between states in inspector

### Ground
- Required for circuit simulation
- Acts as reference node (0V)

## Troubleshooting

### Common Issues

**"Unsupported Ngspice version" Warning**
- This warning is harmless
- PySpice works with newer ngspice versions
- Simulation will still function correctly

**Simulation Not Running**
- Ensure ngspice is installed: `ngspice --version`
- Verify all components have valid values
- Check that circuit has at least one ground component
- Ensure voltage source is connected

**Import Errors**
- Always run from project root: `python3 app.py`
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (3.8+ required)

**Application Won't Start**
- Check for PyQt6 installation: `pip show PyQt6`
- Verify graphics drivers are up to date
- Try running with: `python3 -v app.py` for detailed output

**Undo/Redo Not Working**
- Undo/redo fully supports components, wires, and bend points
- Use `Ctrl+Z` to undo, `Ctrl+Shift+Z` to redo
- Check the Edit menu for undo stack status

## Development

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run with coverage
python3 -m pytest --cov=circuit_designer tests/

# Run specific test
python3 -m pytest tests/test_core.py
```

### Code Quality

The codebase follows professional standards:
- Modular architecture with clear boundaries
- Type hints where appropriate
- Comprehensive error handling
- Undo/redo for all operations
- Memory-efficient spatial indexing

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Performance

- **Efficient Rendering**: Optimized graphics view with minimal redraws
- **Spatial Indexing**: O(1) component collision detection
- **Memory Management**: Proper cleanup of graphics items
- **Lazy Evaluation**: Components only update when necessary

## Limitations

- **AC Analysis**: Currently supports DC analysis only
- **Component Library**: Limited to basic passive and active components
- **Grid Size**: Fixed 15x15 placement grid
- **File Format**: Proprietary .ecis format (JSON-based)

## Future Enhancements

Potential future improvements:
- Additional components (capacitors, inductors, transistors)
- AC and transient analysis
- Oscilloscope view for time-domain analysis
- Component search and filtering
- Netlist export for external simulators

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **PyQt6** - Modern Qt bindings for Python
- **PySpice** - Python interface to ngspice
- **ngspice** - Open source SPICE simulator
- Inspired by modern EDA tools and circuit simulators

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

---

**Version**: 1.0.0
**Status**: Production Ready ✅
**Maintained**: Yes

Built with ❤️ using Python and PyQt6
