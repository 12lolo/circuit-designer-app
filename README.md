# Circuit Designer

A PyQt6-based electronic circuit design and simulation application with PySpice integration.

## ✨ Features

- 🎨 **Visual Circuit Design** - Drag-and-drop component placement
- ⚡ **Circuit Simulation** - Powered by PySpice/ngspice  
- 💾 **Project Management** - Save and load circuit projects
- 🔧 **Component Library** - Resistors, voltage sources, LEDs, switches, and ground
- ↩️ **Undo/Redo** - Full undo/redo support
- 📊 **Simulation Output** - View node voltages and circuit analysis
- ⌨️ **Keyboard Shortcuts** - Efficient workflow

## 🚀 Quick Start

### Installation

1. **Install ngspice** (for circuit simulation):
   ```bash
   # Arch Linux
   sudo pacman -S ngspice

   # Ubuntu/Debian
   sudo apt install ngspice

   # macOS
   brew install ngspice
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Run the Application

```bash
python3 app.py
```

Or use the launcher script:
```bash
./run.sh
```

## 📖 Usage

1. **Add Components**: Drag from the left panel onto the canvas
2. **Connect Wires**: Click connection points (colored dots) to create wires  
3. **Set Values**: Select a component and edit value in Inspect Panel (right side)
4. **Run Simulation**: Press `F5` or click "Run Simulation"

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `F5` | Run simulation |
| `Delete` | Delete selected |
| `R` | Rotate component |
| `Ctrl+=` / `Ctrl+-` | Zoom in/out |

## 📁 Project Structure

```
circuit-designer-app/
├── app.py                    # Application entry point ⭐ Start here
├── circuit_designer/         # Main package
│   ├── core/                 # Core application (main window)
│   ├── components/           # Circuit components (resistor, wire, etc.)
│   ├── simulation/           # PySpice simulation engine
│   ├── ui/                   # User interface
│   │   ├── panels/           # UI panels (components, inspect, log)
│   │   ├── dialogs/          # Dialogs
│   │   ├── widgets/          # Custom widgets
│   │   └── managers/         # Toolbar & shortcut managers
│   ├── project/              # Project & circuit management
│   └── utils/                # Utilities (spatial grid, etc.)
├── tests/                    # Test suite
├── docs/                     # Documentation
└── projects/                 # Your saved projects (.ecis files)
```

## 🔧 Development

### Running Tests

```bash
python3 -m pytest tests/
```

### Code Organization

The codebase was recently reorganized for better maintainability:

- **Before**: Single 1700+ line `main_window.py` file
- **After**: Modular structure with clear separation of concerns

See `docs/REORGANIZATION_PLAN.md` for details.

## 📚 Documentation

- `docs/QUICK_START.md` - Getting started guide
- `docs/REFACTORING_SUMMARY.md` - Code improvements and optimizations
- `docs/REORGANIZATION_PLAN.md` - Project structure details

## ❓ Troubleshooting

**"Unsupported Ngspice version" warning**  
→ This is harmless. PySpice works with newer ngspice versions.

**Simulation not running**  
→ Check: ngspice installed, all components have values, circuit has ground

**Import errors**  
→ Run from project root: `python3 app.py`

## 📝 License

[Add your license]

## 👏 Acknowledgments

- Built with PyQt6
- Simulation: PySpice & ngspice
- Inspired by modern EDA tools

---

**Version**: 1.0.0  
**Status**: Production Ready ✅
