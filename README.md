# ECis-full

A PyQt6-based electronic circuit simulation application for designing and analyzing electronic circuits.

## Features

- **Circuit Design**: Drag and drop electronic components (resistors, voltage sources, current sources, etc.)
- **Interactive Canvas**: Grid-based component placement with snapping
- **Wire Connections**: Connect components with visual wires
- **Component Properties**: Edit component values, names, and orientations
- **Project Management**: Create new, open, and save projects
- **Circuit Simulation**: Run simulations on designed circuits
- **Zoom & Pan**: Navigate large circuit designs easily

## Project Structure

- `main_window.py` - Main application window and core functionality
- `components/` - Circuit component classes and graphics items
- `ui/` - User interface panels and managers
- `.ecis` files - ECis project save files (JSON format)

## Requirements

- Python 3.7+
- PyQt6

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install PyQt6
```

## Usage

Run the application:
```bash
python main_window.py
```

### Keyboard Shortcuts

- `Ctrl+N` - New project
- `Ctrl+O` - Open project
- `Ctrl+S` - Save project
- `F5` - Run simulation
- `Shift+F5` - Stop simulation
- `Ctrl+A` - Select all
- `Ctrl+D` - Deselect all
- `Delete` - Delete selected items
- `R` - Rotate selected component
- `Escape` - Clear selection

## Components

The application supports various electronic components:
- Resistors
- Voltage sources
- Current sources
- Ground connections
- Junction points for wire connections

## File Format

Projects are saved as `.ecis` files in JSON format containing:
- Component data (type, position, value, orientation)
- Wire connection information
- Project metadata

## License

This project is open source.
