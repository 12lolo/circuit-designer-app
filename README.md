# ECis-full

A PyQt6-based electronic circuit simulation application for designing and analyzing electronic circuits.

## Features

### Circuit Design
- **Drag and Drop**: Electronic components (resistors, voltage sources, current sources, etc.)
- **Interactive Canvas**: Grid-based component placement with snapping
- **Wire Connections**: Connect components with visual wires
- **Component Properties**: Edit component values, names, and orientations
- **Rotation**: Rotate components with `R` key (90° increments)

### Editing & Navigation
- **Undo/Redo**: Full undo/redo support for all actions (`Ctrl+Z` / `Ctrl+Shift+Z`)
- **Copy/Paste**: Duplicate components easily (`Ctrl+C` / `Ctrl+V`)
- **Selection Tools**: Select all, deselect, delete selected items
- **Zoom & Pan**: Navigate large circuit designs with mouse wheel or keyboard
- **Middle-click Panning**: Pan the canvas with middle mouse button

### Project Management
- **Visual Project Browser**: Grid view with thumbnails of all projects
- **Search & Filter**: Real-time search to find projects by name
- **Sort Options**: Sort by name (A-Z/Z-A) or last modified (newest/oldest)
- **Auto-save**: Projects automatically save to default directory
- **Export Copies**: Share projects by exporting to any location
- **Project Thumbnails**: Preview circuits before opening
- **Quick Actions**: Right-click to rename or delete projects

### Simulation & Analysis
- **Netlist Generation**: Automatically builds netlists for backend simulation
- **SPICE Export**: Generates SPICE-compatible netlists
- **Circuit Validation**: Detects floating nodes, missing connections, and errors
- **Backend Ready**: Clean API for integration with simulation engines

### Export & Sharing
- **PNG Export**: Export circuit diagrams as high-quality images (`Ctrl+E`)
- **Project Copy**: Save copies for sharing without affecting originals

### Customization
- **Keyboard Shortcuts**: Customize all keyboard shortcuts via Settings menu
- **Shortcuts Manager**: View, edit, and reset shortcuts to defaults
- **Conflict Detection**: Prevents duplicate shortcut assignments

## Project Structure

- `main_window.py` - Main application window and core functionality
- `components/` - Circuit component classes and graphics items
- `ui/` - User interface panels and managers
- `.ecis` files - ECis project save files (JSON format)

## Requirements

- Python 3.7+ (tested newer too; on Arch you may have 3.13)
- PyQt6

Only PyQt6 is currently required (verified by code search – no other third‑party imports).

## Installation (Generic / Cross‑Platform)

1. (Recommended) Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```
2. Upgrade pip (inside the venv):
```bash
python -m pip install --upgrade pip
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the application:
```bash
python main_window.py
```

## Arch Linux Setup
On Arch, Python is system-managed (PEP 668). Installing into the system interpreter without a venv is blocked unless you use --break-system-packages. Prefer one of the safe options below.

### Option A: Use system packages only (quickest)
```bash
sudo pacman -S --needed python python-pyqt6
python main_window.py
```

### Option B: Use pip in a virtual environment (recommended for development)
If `python-pip` is not installed yet:
```bash
sudo pacman -S --needed python-pip
```
Then create & use a venv (keeps global site-packages untouched):
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main_window.py
```

### Option C (NOT recommended): Install into system Python
You could force install with:
```bash
python -m ensurepip --upgrade  # may fail on Arch
python -m pip install --user PyQt6
```
If pip complains about the externally-managed environment, add `--break-system-packages` (but this can cause maintenance headaches). Prefer Options A or B instead.

### Wayland vs X11
If you are on Wayland and encounter rendering issues, try forcing the XCB platform:
```bash
QT_QPA_PLATFORM=xcb python main_window.py
```
Or explicitly use Wayland (if Qt Wayland plugins are installed):
```bash
QT_QPA_PLATFORM=wayland python main_window.py
```

## Usage
Run the application once dependencies are installed:
```bash
python main_window.py
```

### Keyboard Shortcuts

#### File Operations
- `Ctrl+N` - New project
- `Ctrl+O` - Open project (opens project browser)
- `Ctrl+S` - Save project (to default projects directory)
- `Ctrl+Shift+S` - Save copy (to any location for sharing)
- `Ctrl+E` - Export as PNG

#### Editing
- `Ctrl+Z` - Undo
- `Ctrl+Shift+Z` - Redo
- `Ctrl+C` - Copy selected components
- `Ctrl+V` - Paste components
- `Ctrl+A` - Select all
- `Ctrl+D` - Deselect all
- `Delete` - Delete selected items
- `Escape` - Clear selection

#### Component Operations
- `R` - Rotate selected component 90° clockwise
- `Shift+R` - Rotate selected component 90° counter-clockwise

#### View Navigation
- `Ctrl+=` / `Ctrl+-` - Zoom in/out
- `Ctrl+0` - Reset zoom
- `Home` - Center view
- `Arrow keys` - Pan canvas
- `Middle mouse button` - Pan (drag)
- `Ctrl+Mouse wheel` - Zoom

#### Simulation
- `F5` - Run simulation / Generate netlist
- `Shift+F5` - Stop simulation

#### Other
- `F1` - Focus canvas
- `Ctrl+L` - Clear log
- `Ctrl+Shift+C` - Copy simulation output

### Menu Bar

The application includes a full menu bar for easy access to all features:

#### File Menu
- New, Open, Save, Save Copy
- Export as PNG

#### Edit Menu
- Undo, Redo
- Copy, Paste
- Select All, Deselect All

#### View Menu
- Zoom controls
- Center View, Focus Canvas
- Clear Log

#### Simulation Menu
- Run, Stop
- Copy Output

#### Settings Menu
- **Keyboard Shortcuts**: Customize all shortcuts
  - Click on any shortcut to change it
  - Press your desired key combination
  - Reset to defaults button available
  - Conflict detection prevents duplicate shortcuts

#### Help Menu
- About ECis-full

## Components

The application supports various electronic components:
- Resistors
- Voltage sources
- Current sources
- Ground connections
- Junction points for wire connections

## Project Management

### Project Browser
The application features a visual project browser for easy project management:
- **Grid view** with project thumbnails (200x200px previews)
- **Auto-saves** to `~/PycharmProjects/circuit-designer-app/projects/` by default
- **Visual previews** of each project's circuit layout
- **Quick actions**: Double-click to open, right-click to rename/delete
- **Timestamps** showing when each project was last saved

### Saving Projects
- **Save (Ctrl+S)**: Saves to the default projects directory for quick access
- **Save Copy (Ctrl+Shift+S)**: Export a copy anywhere (e.g., Downloads for sharing)
- All projects include embedded thumbnails for the browser

## Backend Integration

The application generates netlists for simulation backends:

```python
# The netlist is generated when pressing F5
netlist = {
    "components": [
        {
            "name": "R1",
            "type": "Resistor",
            "value": "1k",
            "nodes": [
                {"node": "n1", "pin": "in"},
                {"node": "n2", "pin": "out"}
            ]
        },
        ...
    ],
    "nodes": {
        "n0": [...],  # Ground node
        "n1": [...],
        "n2": [...]
    },
    "ground_node": "n0",
    "errors": [...]  # Validation errors/warnings
}
```

The netlist builder (`ui/netlist_builder.py`) provides:
- **Node connectivity analysis**: Automatically groups connected pins into nodes
- **SPICE export**: Convert to SPICE format for simulation
- **Validation**: Detect floating nodes, missing values, disconnected components
- **Clean API**: Easy integration with any simulation engine

To integrate your simulation backend, modify `main_window.py:on_run()` to pass the netlist to your solver.

## File Format

Projects are saved as `.ecis` files in JSON format containing:
- Component data (type, position, value, orientation)
- Wire connection information
- Project metadata (thumbnail, save timestamp, version)

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'PyQt6'` | PyQt6 not installed | Follow Arch Option A or B above |
| `pip: command not found` | `python-pip` not installed on Arch | `sudo pacman -S python-pip` then create venv |
| Qt crashes / blank window on Wayland | Platform plugin mismatch | Set `QT_QPA_PLATFORM=xcb` |

## License

This project is open source.
