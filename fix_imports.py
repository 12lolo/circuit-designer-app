#!/usr/bin/env python3
"""
Script to fix imports after reorganization
"""

import re
from pathlib import Path

# Import mapping: old -> new
IMPORT_MAPPINGS = {
    # Components
    r'from components import': 'from circuit_designer.components import',
    r'from components\.': 'from circuit_designer.components.',
    r'import components': 'import circuit_designer.components',

    # UI
    r'from ui\.components_panel': 'from circuit_designer.ui.panels.components_panel',
    r'from ui\.inspect_panel': 'from circuit_designer.ui.panels.inspect_panel',
    r'from ui\.log_panel': 'from circuit_designer.ui.panels.log_panel',
    r'from ui\.sim_output_panel': 'from circuit_designer.ui.panels.sim_output_panel',
    r'from ui\.project_browser': 'from circuit_designer.ui.panels.project_browser',
    r'from ui\.shortcuts_dialog': 'from circuit_designer.ui.dialogs.shortcuts_dialog',
    r'from ui\.value_input_widget': 'from circuit_designer.ui.widgets.value_input_widget',
    r'from ui\.toolbar_manager': 'from circuit_designer.ui.managers.toolbar_manager',
    r'from ui\.shortcut_manager': 'from circuit_designer.ui.managers.shortcut_manager',
    r'from ui\.quick_access_toolbar': 'from circuit_designer.ui.managers.quick_access_toolbar',
    r'from ui\.canvas_tools': 'from circuit_designer.utils.canvas_tools',
    r'from ui\.constants': 'from circuit_designer.ui.constants',

    # Simulation
    r'from ui\.backend_integration': 'from circuit_designer.simulation.backend_integration',
    r'from ui\.netlist_builder': 'from circuit_designer.simulation.netlist_builder',
    r'from ui\.simulation_engine': 'from circuit_designer.simulation.simulation_engine',
    r'from components\.core import': 'from circuit_designer.simulation.core import',

    # Project
    r'from ui\.project_manager': 'from circuit_designer.project.project_manager',
    r'from ui\.circuit_manager': 'from circuit_designer.project.circuit_manager',
    r'from ui\.undo_commands': 'from circuit_designer.project.undo_commands',

    # Utils
    r'from ui\.spatial_grid': 'from circuit_designer.utils.spatial_grid',
}

def fix_imports_in_file(filepath):
    """Fix imports in a single file"""
    try:
        content = filepath.read_text()
        original = content

        for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_pattern, content)

        if content != original:
            filepath.write_text(content)
            print(f"✓ Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error in {filepath}: {e}")
        return False

def main():
    """Main function"""
    root = Path(__file__).parent / 'circuit_designer'

    # Find all Python files
    py_files = list(root.rglob('*.py'))

    fixed_count = 0
    for filepath in py_files:
        if fix_imports_in_file(filepath):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
