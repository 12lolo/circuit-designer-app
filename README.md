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

- `Ctrl+N` - New project
- `Ctrl+O` - Open project
- `Ctrl+S` - Save project
- `F5` - Run simulation
- `Shift+F5` - Stop simulation
- `Ctrl+A` - Select all
- `Ctrl+D` - Deselect all
- `Delete` - Delete selected items
- `R` - Rotate selected component (Shift+R for opposite direction)
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

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'PyQt6'` | PyQt6 not installed | Follow Arch Option A or B above |
| `pip: command not found` | `python-pip` not installed on Arch | `sudo pacman -S python-pip` then create venv |
| Qt crashes / blank window on Wayland | Platform plugin mismatch | Set `QT_QPA_PLATFORM=xcb` |

## License

This project is open source.
