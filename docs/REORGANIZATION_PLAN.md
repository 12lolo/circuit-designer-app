# Circuit Designer - Code Reorganization Plan

## Current Structure (Before)
```
circuit-designer-app/
├── main_window.py (1747 lines - TOO LARGE!)
├── test_core_manual.py
├── run.sh
├── README.md
├── requirements.txt
├── components/
│   ├── __init__.py
│   ├── component_item.py (676 lines)
│   ├── connection_points.py (217 lines)
│   ├── core.py (310 lines)
│   ├── draggable_button.py
│   ├── graphics_view.py
│   └── wire.py (295 lines)
├── ui/
│   ├── __init__.py
│   ├── backend_integration.py (284 lines)
│   ├── canvas_tools.py
│   ├── circuit_manager.py (NEW)
│   ├── components_panel.py
│   ├── constants.py (NEW)
│   ├── inspect_panel.py
│   ├── log_panel.py
│   ├── netlist_builder.py
│   ├── project_browser.py
│   ├── project_manager.py
│   ├── quick_access_toolbar.py
│   ├── shortcut_manager.py
│   ├── shortcuts_dialog.py
│   ├── sim_output_panel.py
│   ├── simulation_engine.py
│   ├── spatial_grid.py (NEW)
│   ├── toolbar_manager.py
│   ├── undo_commands.py
│   └── value_input_widget.py
└── projects/ (user projects)
```

## Problems:
1. **main_window.py is 1747 lines** - should be ~300-500 lines max
2. **No clear separation** between app logic and UI
3. **No proper entry point** - main_window.py is both entry point and main class
4. **Mixed responsibilities** in main_window
5. **Test file at root level** - should be in tests/ folder

## New Structure (After)
```
circuit-designer-app/
├── app.py                          # NEW: Clean entry point
├── README.md
├── requirements.txt
├── run.sh
│
├── circuit_designer/               # NEW: Main application package
│   ├── __init__.py
│   │
│   ├── core/                       # NEW: Core application logic
│   │   ├── __init__.py
│   │   ├── main_window.py          # Slimmed down (~400 lines)
│   │   ├── event_handlers.py       # NEW: Event handling
│   │   ├── menu_actions.py         # NEW: Menu action handlers
│   │   └── scene_manager.py        # NEW: Scene/canvas management
│   │
│   ├── components/                 # Component models (existing, cleaned)
│   │   ├── __init__.py
│   │   ├── component_item.py
│   │   ├── connection_points.py
│   │   ├── wire.py
│   │   ├── draggable_button.py
│   │   └── graphics_view.py
│   │
│   ├── simulation/                 # NEW: Simulation engine
│   │   ├── __init__.py
│   │   ├── core.py                 # PySpice integration
│   │   ├── backend_integration.py
│   │   ├── netlist_builder.py
│   │   └── circuit_transformer.py
│   │
│   ├── ui/                         # UI panels and widgets
│   │   ├── __init__.py
│   │   ├── panels/                 # NEW: UI panels subfolder
│   │   │   ├── __init__.py
│   │   │   ├── components_panel.py
│   │   │   ├── inspect_panel.py
│   │   │   ├── log_panel.py
│   │   │   ├── sim_output_panel.py
│   │   │   └── project_browser.py
│   │   │
│   │   ├── dialogs/                # NEW: Dialogs subfolder
│   │   │   ├── __init__.py
│   │   │   └── shortcuts_dialog.py
│   │   │
│   │   ├── widgets/                # NEW: Custom widgets
│   │   │   ├── __init__.py
│   │   │   └── value_input_widget.py
│   │   │
│   │   ├── managers/               # NEW: UI managers
│   │   │   ├── __init__.py
│   │   │   ├── toolbar_manager.py
│   │   │   └── shortcut_manager.py
│   │   │
│   │   └── constants.py            # UI constants
│   │
│   ├── project/                    # NEW: Project management
│   │   ├── __init__.py
│   │   ├── project_manager.py
│   │   ├── circuit_manager.py      # Save/load circuits
│   │   └── undo_commands.py        # Undo/redo system
│   │
│   └── utils/                      # NEW: Utilities
│       ├── __init__.py
│       ├── spatial_grid.py         # Optimized component placement
│       └── canvas_tools.py         # Canvas helpers
│
├── tests/                          # NEW: Test folder
│   ├── __init__.py
│   ├── test_core.py                # Renamed from test_core_manual.py
│   ├── test_components.py
│   └── test_simulation.py
│
├── docs/                           # NEW: Documentation
│   ├── REFACTORING_SUMMARY.md
│   ├── QUICK_START.md
│   └── USER_GUIDE.md
│
├── projects/                       # User project files (.ecis)
│   └── (user created projects)
│
└── venv/                           # Virtual environment (unchanged)
```

## Key Changes:

### 1. **New `app.py` Entry Point**
Clean, simple entry point:
```python
from circuit_designer.core.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
```

### 2. **Split main_window.py** (1747 → ~400 lines)
Extract to new modules:
- `event_handlers.py` - Mouse, keyboard, drag/drop events (~300 lines)
- `menu_actions.py` - File, Edit, View menu actions (~400 lines)
- `scene_manager.py` - Scene initialization, grid drawing (~200 lines)

### 3. **Organized Subpackages**
- `core/` - Main application logic
- `simulation/` - All simulation-related code
- `ui/` - Better organized UI components
  - `panels/` - Side panels
  - `dialogs/` - Popup dialogs
  - `widgets/` - Custom widgets
  - `managers/` - Toolbar, shortcuts, etc.
- `project/` - Project and circuit management
- `utils/` - Helper utilities

### 4. **Tests Folder**
Move tests out of root into proper `tests/` folder

### 5. **Docs Folder**
Keep documentation separate from code

## Benefits:

✅ **Smaller files** - Each file < 500 lines, easier to maintain
✅ **Clear separation** - Logic, UI, simulation, project management
✅ **Better imports** - `from circuit_designer.ui.panels import InspectPanel`
✅ **Easier testing** - Tests in dedicated folder
✅ **Professional structure** - Matches Python best practices
✅ **Scalable** - Easy to add new features
✅ **Better navigation** - Find code faster

## Migration Steps:

1. Create new folder structure
2. Move files to new locations
3. Split main_window.py into modules
4. Update all imports
5. Create new __init__.py files
6. Test that app still works
7. Update documentation

## Estimated Time: 2-3 hours

This will make your codebase much more maintainable and professional!
