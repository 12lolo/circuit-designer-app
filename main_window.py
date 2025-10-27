import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGraphicsScene, QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QPointF, QSettings, QEvent
from PyQt6.QtGui import QPen, QColor, QUndoStack

from components import (
    Wire, JunctionPoint,
    ComponentItem, DroppableGraphicsView
)

# Import the new UI components
from ui.components_panel import ComponentsPanel
from ui.inspect_panel import InspectPanel
from ui.toolbar_manager import ToolbarManager
from ui.simulation_engine import SimulationEngine
from ui.canvas_tools import CanvasTools
from ui.log_panel import LogPanel
from ui.sim_output_panel import SimulationOutputPanel
from ui.project_manager import ProjectManager
from ui.project_browser import ProjectBrowserDialog
from ui.netlist_builder import NetlistBuilder
from ui.shortcuts_dialog import ShortcutsDialog
from ui.undo_commands import (
    AddComponentCommand, DeleteComponentCommand, MoveComponentCommand,
    RotateComponentCommand, AddWireCommand, DeleteWireCommand, MultiDeleteCommand
)
from ui.quick_access_toolbar import make_menu_pinnable
from ui.backend_integration import BackendSimulator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize component managers
        self.components_panel = None
        self.inspect_panel = None
        self.sim_output_panel = None
        self.toolbar_manager = None
        self.simulation_engine = None
        self.canvas_tools = None
        self.log_panel = None

        # Track selected items for deletion
        self.selected_items = []
        self.selected_component = None

        # Floating controls
        self._floating_controls = None

        # Project management
        self.project_manager = ProjectManager()
        self.current_project_name = None  # Track current project filename

        # Undo/Redo system
        self.undo_stack = QUndoStack(self)

        # Netlist builder for backend integration
        self.netlist_builder = NetlistBuilder()

        # Backend simulator for PySpice integration
        self.backend_simulator = BackendSimulator()

        # Clipboard for copy/paste
        self.clipboard_data = None

        # Track unsaved changes
        self.has_unsaved_changes = False

        self.setupUi()

        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setupUi(self):
        # Main window properties
        self.setWindowTitle("ECis-full")
        self.setGeometry(0, 0, 1200, 750)

        # Central widget
        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)

        # Main vertical layout
        self.verticalLayout_central = QVBoxLayout(self.centralwidget)

        # Create the existing horizontal splitter (three panels side-by-side)
        self.splitterMain = QSplitter(Qt.Orientation.Horizontal)

        # NEW: wrap horizontal splitter + log panel inside a vertical splitter for resizable log height
        self.mainVerticalSplitter = QSplitter(Qt.Orientation.Vertical)
        self.mainVerticalSplitter.addWidget(self.splitterMain)
        self.verticalLayout_central.addWidget(self.mainVerticalSplitter)

        # Setup the three main sections into splitterMain
        self.setupComponentsSection()
        self.setupSandboxSection()
        self.setupInspectSection()

        # Setup log section (will add log panel as second widget of vertical splitter)
        self.setupLogSection()

        # Setup toolbar and connect signals
        self.setupToolbarAndConnections()

        # Connect undo stack to track changes
        self.undo_stack.indexChanged.connect(self.on_undo_stack_changed)

        # Stretch factors: give more space to upper area initially
        self.mainVerticalSplitter.setStretchFactor(0, 5)
        self.mainVerticalSplitter.setStretchFactor(1, 1)

        # After full UI init, normalize connection points (in case of hot reload / persisted state)
        if hasattr(self, 'refresh_all_component_connection_points'):
            self.refresh_all_component_connection_points()

    def setupComponentsSection(self):
        """Setup the Components (Componenten) section"""
        self.components_panel = ComponentsPanel()
        self.splitterMain.addWidget(self.components_panel)

    def setupSandboxSection(self):
        """Setup the Sandbox (Zandbak) section"""
        from PyQt6.QtWidgets import QGroupBox

        self.groupSandbox = QGroupBox("Canvas")
        self.splitterMain.addWidget(self.groupSandbox)

        self.horizontalLayout_sandbox = QHBoxLayout(self.groupSandbox)

        # Graphics view
        self.graphicsViewSandbox = DroppableGraphicsView(self)
        self.horizontalLayout_sandbox.addWidget(self.graphicsViewSandbox)

        # Canvas tools controller (no sidebar layout; use floating controls instead)
        self.canvas_tools = CanvasTools()

        # Setup graphics scene
        self.scene = QGraphicsScene(self)
        self.graphicsViewSandbox.setScene(self.scene)

        # Initialize simulation engine
        self.simulation_engine = SimulationEngine(self.graphicsViewSandbox)

        # Draw grid
        self.drawGrid()

        # Connect canvas tool signals (zoom in/out + probe retained)
        self.canvas_tools.zoom_in_requested.connect(self.on_zoom_in)
        self.canvas_tools.zoom_out_requested.connect(self.on_zoom_out)
        self.canvas_tools.probe_requested.connect(self.on_probe)
        # Connect new floating run/clear actions
        self.canvas_tools.run_requested.connect(self.on_run)
        self.canvas_tools.clear_requested.connect(self.on_clear_sandbox)

        # Create floating controls overlay and position it
        try:
            self._floating_controls = self.canvas_tools.get_floating_widget(self.graphicsViewSandbox.viewport())
            self._position_floating_controls()
            # Track viewport resizes to reposition overlay
            self.graphicsViewSandbox.viewport().installEventFilter(self)
            # Also track panning via scrollbars to keep overlay attached to viewport corners
            try:
                self.graphicsViewSandbox.horizontalScrollBar().valueChanged.connect(lambda _: self._position_floating_controls())
                self.graphicsViewSandbox.verticalScrollBar().valueChanged.connect(lambda _: self._position_floating_controls())
            except Exception:
                pass
        except Exception:
            # Fallback: ignore floating controls if creation fails
            self._floating_controls = None

    def _position_floating_controls(self):
        """Place floating controls at a corner inside the canvas viewport, based on its current anchor."""
        if self._floating_controls is None:
            return
        try:
            # Prefer anchor-based repositioning if available (draggable snapping)
            if hasattr(self._floating_controls, 'reposition_to_anchor'):
                # Ensure size hint is realized before computing anchor positions
                self._floating_controls.adjustSize()
                self._floating_controls.reposition_to_anchor()
                return
        except Exception:
            pass
        # Fallback: top-left margin
        margin_x = 10
        margin_y = 10
        self._floating_controls.adjustSize()
        self._floating_controls.move(margin_x, margin_y)
        self._floating_controls.raise_()
        self._floating_controls.show()

    def eventFilter(self, obj, event):
        # Reposition floating controls when the canvas viewport resizes
        if obj is getattr(self.graphicsViewSandbox, 'viewport', lambda: None)() and event.type() == QEvent.Type.Resize:
            self._position_floating_controls()
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure overlay is positioned after initial show and layout
        try:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._position_floating_controls)
        except Exception:
            self._position_floating_controls()

    def drawGrid(self):
        """Draw the grid on the graphics scene with an outer non-placeable border.
        Visual grid: (placement_cells + 2) cells per side (adds 1 cell border on each side).
        Placement grid (where components may snap/occupy): placement_cells per side (original 15).
        Components are clamped to placement grid via graphicsViewSandbox.grid_rect.
        """
        # Configuration
        placement_cells = 15
        border_thickness_cells = 1  # one cell each side
        visual_cells = placement_cells + 2 * border_thickness_cells

        # Base scene dimension previously 1000x600 leading to blank space; derive spacing from a square target height
        # Keep same spacing logic so internal cell size stable relative to previous behavior.
        target_height = 600  # legacy vertical dimension baseline
        grid_spacing = target_height / placement_cells  # cell size

        # Dimensions
        placement_width = placement_cells * grid_spacing
        placement_height = placement_cells * grid_spacing
        visual_width = visual_cells * grid_spacing
        visual_height = visual_cells * grid_spacing

        # Offsets (centered at origin). Placement rect inset by 1 cell within visual rect
        placement_left = -placement_width / 2
        placement_top = -placement_height / 2
        visual_left = -visual_width / 2
        visual_top = -visual_height / 2

        # Clear ONLY previous grid lines (keep components if re-drawing). Detect by custom data flag.
        for item in self.scene.items():
            try:
                if hasattr(item, 'data') and item.data(0) in ('grid', 'grid-border'):
                    self.scene.removeItem(item)
            except Exception:
                pass

        # Update graphics view spacing
        self.graphicsViewSandbox.grid_spacing = grid_spacing

        # Store placement bounds for snapping/clamping (used by components)
        self.graphicsViewSandbox.grid_rect = (placement_left, placement_top, placement_width, placement_height)
        # Store visual bounds (for potential future use like centering, limiting panning)
        self.graphicsViewSandbox.visual_grid_rect = (visual_left, visual_top, visual_width, visual_height)

        # Shrink scene rect to visual grid (minimal blank area)
        self.scene.setSceneRect(visual_left, visual_top, visual_width, visual_height)

        light_pen = QPen(QColor(220, 220, 220))
        inner_border_pen = QPen(QColor(180, 180, 180))
        outer_border_pen = QPen(QColor(80, 80, 80), 2)

        # Helper to add line with tag
        def add_line(x1, y1, x2, y2, pen):
            line_item = self.scene.addLine(x1, y1, x2, y2, pen)
            try:
                line_item.setData(0, 'grid')
            except Exception:
                pass

        # Draw full visual grid lines
        for i in range(visual_cells + 1):  # lines count = cells + 1
            x = visual_left + i * grid_spacing
            pen = light_pen
            # Vertical outer border
            if i == 0 or i == visual_cells:
                pen = outer_border_pen
            # Placement border (inner ring) thicker/darker than inner lines
            elif i == border_thickness_cells or i == visual_cells - border_thickness_cells:
                pen = inner_border_pen
            add_line(x, visual_top, x, visual_top + visual_height, pen)

        for i in range(visual_cells + 1):
            y = visual_top + i * grid_spacing
            pen = light_pen
            if i == 0 or i == visual_cells:
                pen = outer_border_pen
            elif i == border_thickness_cells or i == visual_cells - border_thickness_cells:
                pen = inner_border_pen
            add_line(visual_left, y, visual_left + visual_width, y, pen)

        # Add shaded forbidden border rectangles
        from PyQt6.QtGui import QBrush
        from PyQt6.QtWidgets import QGraphicsRectItem
        shaded_brush = QBrush(QColor(50, 50, 50, 40))
        def add_shaded_rect(x, y, w, h):
            rect_item = QGraphicsRectItem(x, y, w, h)
            rect_item.setBrush(shaded_brush)
            rect_item.setPen(QPen(Qt.PenStyle.NoPen))
            rect_item.setZValue(-10)  # behind grid lines
            rect_item.setData(0, 'grid-border')
            self.scene.addItem(rect_item)
        # Left border
        add_shaded_rect(visual_left, visual_top, grid_spacing, visual_height)
        # Right border
        add_shaded_rect(placement_left + placement_width, visual_top, grid_spacing, visual_height)
        # Top border
        add_shaded_rect(visual_left + grid_spacing, visual_top, placement_width, grid_spacing)
        # Bottom border
        add_shaded_rect(visual_left + grid_spacing, placement_top + placement_height, placement_width, grid_spacing)

        # Optional: subtle shaded overlay for forbidden border cells (visual only)
        # (Skippable for now; can add semi-transparent rects if desired.)

        # Center view on grid after redraw (preserve if user already working? keep simple now)
        self.graphicsViewSandbox.centerOn(0, 0)
        # Enforce new min zoom immediately
        if hasattr(self.graphicsViewSandbox, 'update_min_zoom'):
            self.graphicsViewSandbox.update_min_zoom()

    def setupInspectSection(self):
        """Setup the Inspect section with Simulation Output beneath it"""
        # Use a vertical splitter so the user can resize Inspect vs. Output
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Inspect panel (top)
        self.inspect_panel = InspectPanel()
        self.right_splitter.addWidget(self.inspect_panel)

        # Simulation output panel (bottom)
        self.sim_output_panel = SimulationOutputPanel()
        self.right_splitter.addWidget(self.sim_output_panel)

        # Add to main horizontal splitter as the right pane
        self.splitterMain.addWidget(self.right_splitter)

        # Set initial proportions (more space to Inspect by default)
        self.right_splitter.setStretchFactor(0, 3)
        self.right_splitter.setStretchFactor(1, 1)
        try:
            # Try to restore last sizes; if none, apply a default split
            settings = QSettings("ECis", "CircuitDesigner")
            sizes_json = settings.value("right_splitter_sizes", "")
            if sizes_json:
                import json as _json
                sizes = _json.loads(sizes_json)
                if isinstance(sizes, list) and all(isinstance(x, int) for x in sizes):
                    self.right_splitter.setSizes(sizes)
                else:
                    self.right_splitter.setSizes([500, 160])
            else:
                self.right_splitter.setSizes([500, 160])
        except Exception:
            pass

        # Connect inspect and output panel signals
        self.inspect_panel.field_changed.connect(self.on_inspect_field_changed)
        self.sim_output_panel.copy_output_requested.connect(self.on_copy_output_clicked)
        self.sim_output_panel.node_clicked.connect(self.on_node_clicked)

    def setupLogSection(self):
        """Setup the Log section (placed in vertical splitter for resizable height)"""
        self.log_panel = LogPanel()
        # Instead of adding directly to the vertical layout, add as second pane of vertical splitter
        if hasattr(self, 'mainVerticalSplitter'):
            self.mainVerticalSplitter.addWidget(self.log_panel)
            # Optional: minimum height so it can collapse but not disappear entirely
            self.log_panel.setMinimumHeight(60)
        else:
            # Fallback (should not happen) – keep old behavior
            self.verticalLayout_central.addWidget(self.log_panel)

    def setupToolbarAndConnections(self):
        """Setup toolbar and connect all signals"""
        self.toolbar_manager = ToolbarManager(self)

        # Setup menu bar
        self.setup_menu_bar()

        # Connect toolbar signals
        self.toolbar_manager.new_requested.connect(self.on_new)
        self.toolbar_manager.open_requested.connect(self.on_open)
        self.toolbar_manager.save_requested.connect(self.on_save)
        self.toolbar_manager.save_copy_requested.connect(self.on_save_copy)
        self.toolbar_manager.undo_requested.connect(self.undo_stack.undo)
        self.toolbar_manager.redo_requested.connect(self.undo_stack.redo)
        self.toolbar_manager.run_requested.connect(self.on_run)
        self.toolbar_manager.stop_requested.connect(self.on_stop)

        # Connect additional action signals
        self.toolbar_manager.copy_requested.connect(self.on_copy)
        self.toolbar_manager.paste_requested.connect(self.on_paste)
        self.toolbar_manager.copy_output_requested.connect(self.on_copy_output_clicked)
        self.toolbar_manager.select_all_requested.connect(self.on_select_all)
        self.toolbar_manager.deselect_all_requested.connect(self.on_deselect_all)
        self.toolbar_manager.focus_canvas_requested.connect(self.on_focus_canvas)
        self.toolbar_manager.clear_log_requested.connect(self.on_clear_log)
        self.toolbar_manager.zoom_in_requested.connect(self.on_zoom_in)
        self.toolbar_manager.zoom_out_requested.connect(self.on_zoom_out)
        self.toolbar_manager.zoom_reset_requested.connect(self.on_zoom_reset)
        self.toolbar_manager.center_view_requested.connect(self.on_center_view)
        self.toolbar_manager.export_png_requested.connect(self.on_export_png)
        # Removed: clear sandbox action is now in floating controls
        # self.toolbar_manager.clear_sandbox_requested.connect(self.on_clear_sandbox)

    def setup_menu_bar(self):
        """Setup the menu bar with pinnable items"""
        menubar = self.menuBar()
        toolbar = self.toolbar_manager.toolbar

        # File menu
        file_menu = menubar.addMenu("&File")
        make_menu_pinnable(file_menu, toolbar, self.toolbar_manager.actionNieuw, "New")
        make_menu_pinnable(file_menu, toolbar, self.toolbar_manager.actionOpenen, "Open")
        make_menu_pinnable(file_menu, toolbar, self.toolbar_manager.actionOpslaan, "Save")
        make_menu_pinnable(file_menu, toolbar, self.toolbar_manager.actionSaveCopy, "Save Copy")
        file_menu.addSeparator()
        make_menu_pinnable(file_menu, toolbar, self.toolbar_manager.actionExportPNG, "Export PNG")

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionUndo, "Undo")
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionRedo, "Redo")
        edit_menu.addSeparator()
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionCopy, "Copy")
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionPaste, "Paste")
        edit_menu.addSeparator()
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionSelectAll, "Select All")
        make_menu_pinnable(edit_menu, toolbar, self.toolbar_manager.actionDeselectAll, "Deselect All")

        # View menu
        view_menu = menubar.addMenu("&View")
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionZoomIn, "Zoom In")
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionZoomOut, "Zoom Out")
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionZoomReset, "Reset Zoom")
        view_menu.addSeparator()
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionCenterView, "Center View")
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionFocusCanvas, "Focus Canvas")
        view_menu.addSeparator()
        make_menu_pinnable(view_menu, toolbar, self.toolbar_manager.actionClearLog, "Clear Log")

        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")
        make_menu_pinnable(sim_menu, toolbar, self.toolbar_manager.actionRun, "Run")
        make_menu_pinnable(sim_menu, toolbar, self.toolbar_manager.actionStop, "Stop")
        sim_menu.addSeparator()
        make_menu_pinnable(sim_menu, toolbar, self.toolbar_manager.actionCopyOutput, "Copy Output")

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        shortcuts_action = settings_menu.addAction("Keyboard Shortcuts...")
        shortcuts_action.triggered.connect(self.on_show_shortcuts_dialog)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("About ECis-full")
        about_action.triggered.connect(self.on_about)

    def on_show_shortcuts_dialog(self):
        """Show the keyboard shortcuts settings dialog"""
        dialog = ShortcutsDialog(self.toolbar_manager, self)
        dialog.exec()

    def on_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About ECis-full",
            "<h2>ECis-full</h2>"
            "<p>A PyQt6-based electronic circuit simulation application.</p>"
            "<p>Version 1.0</p>"
            "<p>For designing and analyzing electronic circuits with "
            "visual netlist generation and simulation support.</p>"
        )

    def on_undo_stack_changed(self):
        """Called when undo stack changes (indicates unsaved changes)"""
        self.mark_as_changed()

    def mark_as_changed(self):
        """Mark the project as having unsaved changes"""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.update_window_title()

    def mark_as_saved(self):
        """Mark the project as saved"""
        self.has_unsaved_changes = False
        self.update_window_title()

    def update_window_title(self):
        """Update window title to show project name and unsaved status"""
        title = "ECis-full"
        if self.current_project_name:
            title += f" - {self.current_project_name}"
        if self.has_unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def keyPressEvent(self, event):
        """Enhanced keyboard event handling"""
        key = event.key()
        modifiers = event.modifiers()

        # Handle component rotation for selected items (with undo support)
        if key == Qt.Key.Key_R and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self.selected_component and hasattr(self.selected_component, 'component_type'):
                angle = -90 if modifiers & Qt.KeyboardModifier.ShiftModifier else 90
                command = RotateComponentCommand(self.selected_component, angle, f"Rotate {self.selected_component.component_type}")
                self.undo_stack.push(command)
                event.accept()
                return

        # Handle Escape key to deselect all
        if key == Qt.Key.Key_Escape:
            self.on_deselect_all()
            event.accept()
            return

        # Pass Delete key to existing handler
        if key == Qt.Key.Key_Delete:
            self.delete_selected_components()
            event.accept()
            return

        # Pass other events to parent
        super().keyPressEvent(event)

    # Action handlers
    def on_new(self):
        """Create a new project by clearing the scene"""
        # Ask for confirmation if there are items in the scene
        if self.scene.items():
            reply = QMessageBox.question(
                self,
                'New Project',
                'Start a new project? All unsaved changes will be lost.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Clear the scene
        self.scene.clear()

        # Redraw the grid
        self.drawGrid()

        # Clear inspect panel and reset selection
        self.selected_component = None
        if self.sim_output_panel:
            self.sim_output_panel.clear_output()
        self.inspect_panel.show_default_state()

        # Reset project name and clear undo stack
        self.current_project_name = None
        self.undo_stack.clear()
        self.mark_as_saved()

        self.log_panel.log_message("[INFO] New project started")

    def on_clear_sandbox(self):
        """Clear all items from the sandbox after confirmation and redraw the grid."""
        reply = QMessageBox.question(
            self,
            'Clear Sandbox',
            'Are you sure you want to clear the sandbox?\nAll components and wires will be removed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Clear the scene and redraw grid
        self.scene.clear()
        self.drawGrid()

        # Reset selection and panels
        self.selected_component = None
        if self.sim_output_panel:
            self.sim_output_panel.clear_output()
        if self.inspect_panel:
            self.inspect_panel.show_default_state()

        if hasattr(self, 'log_panel'):
            self.log_panel.log_message('[INFO] Sandbox cleared')

    def _get_next_project_name(self):
        """Generate the next available project name (ECIS_Project_1, ECIS_Project_2, etc.)"""
        projects_dir = self.project_manager.default_project_dir
        counter = 1

        while True:
            name = f"ECIS_Project_{counter}"
            filepath = projects_dir / f"{name}.ecis"

            if not filepath.exists():
                return name

            counter += 1

            # Safety limit
            if counter > 9999:
                return f"ECIS_Project_{counter}"

    def serialize_project_data(self):
        """Serialize the current project data to a dictionary"""
        project_data = {
            "version": "1.0",
            "components": [],
            "wires": []
        }

        # Collect all components and wires from the scene
        for item in self.scene.items():
            if hasattr(item, 'component_type'):  # It's a component
                component_data = {
                    "type": item.component_type,
                    "name": getattr(item, 'name', item.component_type),
                    "value": getattr(item, 'value', ''),
                    "position": {
                        "x": item.x(),
                        "y": item.y()
                    },
                    "orientation": getattr(item, 'orientation', 0),
                    "size": {
                        "width": getattr(item, 'size_w', 1),
                        "height": getattr(item, 'size_h', 1)
                    }
                }
                project_data["components"].append(component_data)

            elif isinstance(item, Wire):  # It's a wire
                # Get the connection points
                start_point = item.start_point
                end_point = item.end_point

                wire_data = {
                    "start": {
                        "x": start_point.scenePos().x(),
                        "y": start_point.scenePos().y(),
                        "component_id": self.get_component_id_for_point(start_point)
                    },
                    "end": {
                        "x": end_point.scenePos().x(),
                        "y": end_point.scenePos().y(),
                        "component_id": self.get_component_id_for_point(end_point)
                    }
                }
                project_data["wires"].append(wire_data)

        return project_data

    def get_component_id_for_point(self, point):
        """Get a unique identifier for the component that owns a connection point"""
        if hasattr(point, 'parent_component'):
            component = point.parent_component
            return f"{component.component_type}_{component.x()}_{component.y()}"
        return None

    def deserialize_project_data(self, project_data):
        """Load project data from a dictionary"""
        # Clear the current scene
        self.scene.clear()
        self.drawGrid()

        # Keep track of components for wire reconstruction
        component_map = {}

        # Load components
        for comp_data in project_data.get("components", []):
            try:
                # Create component based on type
                component_type = comp_data["type"]
                size_w = comp_data["size"]["width"]
                size_h = comp_data["size"]["height"]

                # Create the component
                component = ComponentItem(component_type, size_w, size_h, self.graphicsViewSandbox.grid_spacing)

                # Set properties
                component.name = comp_data.get("name", component_type)
                component.value = comp_data.get("value", "")
                component.orientation = comp_data.get("orientation", 0)

                # Set position
                pos = comp_data["position"]
                component.setPos(pos["x"], pos["y"])

                # Apply rotation via method to ensure connection points correct
                if component.orientation:
                    component.rotate_component(0)  # triggers recreation with same orientation

                # Add to scene
                self.scene.addItem(component)

                # Store in component map for wire reconstruction
                component_id = f"{component_type}_{pos['x']}_{pos['y']}"
                component_map[component_id] = component

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Error loading component: {e}")

        # Load wires (simplified approach - just create wires between points)
        for wire_data in project_data.get("wires", []):
            try:
                # For now, create junction points at wire positions
                # In a more complete implementation, you'd reconstruct the exact wire connections
                start_pos = wire_data["start"]
                end_pos = wire_data["end"]

                # Create junction points
                start_junction = JunctionPoint(QPointF(start_pos["x"], start_pos["y"]))
                end_junction = JunctionPoint(QPointF(end_pos["x"], end_pos["y"]))

                self.scene.addItem(start_junction)
                self.scene.addItem(end_junction)

                # Create wire between junction points
                wire = Wire(start_junction, end_junction)
                self.scene.addItem(wire)

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Error loading wire: {e}")

        # After loading, ensure all connection points use latest layout
        self.refresh_all_component_connection_points()

    def on_open(self):
        """Open an existing project using the project browser"""
        # Ask for confirmation if there are unsaved changes
        if self.scene.items():
            reply = QMessageBox.question(
                self,
                'Open Project',
                'Open a project? All unsaved changes will be lost.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Show project browser dialog
        browser = ProjectBrowserDialog(self.project_manager, self)
        if browser.exec() == QDialog.DialogCode.Accepted:
            filepath = browser.get_selected_project_path()
            if filepath:
                try:
                    # Load project data
                    project_data = self.project_manager.load_project(filepath)

                    if project_data:
                        # Deserialize and load the project data
                        self.deserialize_project_data(project_data)

                        # Set current project name
                        self.current_project_name = filepath.name

                        # Clear undo stack and mark as saved
                        self.undo_stack.clear()
                        self.mark_as_saved()

                        # Clear selection and update UI
                        self.selected_component = None
                        self.inspect_panel.show_default_state()

                        self.log_panel.log_message(f"[INFO] Project loaded: {self.current_project_name}")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to load project file")
                        self.log_panel.log_message(f"[ERROR] Failed to load project")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error opening project: {e}")
                    self.log_panel.log_message(f"[ERROR] Error opening project: {e}")

    def on_save(self):
        """Save the current project to the default projects directory"""
        # If no current project name, ask for one
        if not self.current_project_name:
            self.current_project_name = self._prompt_for_project_name()
            if not self.current_project_name:
                return  # User cancelled

        # Check for file collision
        filepath = self.project_manager.default_project_dir / self.current_project_name
        if filepath.exists():
            reply = QMessageBox.question(
                self,
                'File Already Exists',
                f"A project named '{self.current_project_name}' already exists.\n\n"
                f"Do you want to replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                # Ask for a new name
                self.current_project_name = self._prompt_for_project_name(self.current_project_name)
                if not self.current_project_name:
                    return  # User cancelled

                # Recursively call on_save with the new name
                return self.on_save()

        try:
            # Serialize the project data
            project_data = self.serialize_project_data()

            # Get grid rect for thumbnail
            grid_rect = getattr(self.graphicsViewSandbox, 'visual_grid_rect', None)

            # Save using project manager
            success = self.project_manager.save_project(
                project_data,
                self.current_project_name,
                self.scene,
                grid_rect=grid_rect
            )

            if success:
                self.mark_as_saved()
                self.log_panel.log_message(f"[INFO] Project saved: {self.current_project_name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save project")
                self.log_panel.log_message(f"[ERROR] Failed to save project")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving project: {e}")
            self.log_panel.log_message(f"[ERROR] Error saving project: {e}")

    def _prompt_for_project_name(self, default_name=None):
        """Prompt user for a project name"""
        from PyQt6.QtWidgets import QInputDialog

        # Generate default name with auto-increment if not provided
        if default_name is None:
            default_name = self._get_next_project_name()

        name, ok = QInputDialog.getText(
            self,
            "Save Project",
            "Enter project name:",
            text=default_name
        )

        if not ok or not name.strip():
            return None

        project_name = name.strip()
        if not project_name.endswith('.ecis'):
            project_name += '.ecis'

        return project_name

    def on_save_copy(self):
        """Save a copy of the project to any location (for sharing)"""
        # Show file dialog to select a location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Copy",
            os.path.expanduser("~/Downloads/ECis-project.ecis"),
            "ECis Project Files (*.ecis);;All Files (*)"
        )

        if file_path:
            try:
                # Serialize the project data
                project_data = self.serialize_project_data()

                # Get grid rect for thumbnail
                grid_rect = getattr(self.graphicsViewSandbox, 'visual_grid_rect', None)

                # Save copy using project manager
                success = self.project_manager.save_project_copy(
                    project_data,
                    file_path,
                    self.scene,
                    grid_rect=grid_rect
                )

                if success:
                    self.log_panel.log_message(f"[INFO] Copy saved to: {os.path.basename(file_path)}")
                    QMessageBox.information(
                        self,
                        "Saved",
                        f"Project copy successfully saved to:\n{os.path.basename(file_path)}"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to save project copy")
                    self.log_panel.log_message(f"[ERROR] Failed to save copy")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving copy: {e}")
                self.log_panel.log_message(f"[ERROR] Error saving copy: {e}")

    def on_run(self):
        self.log_panel.log_message("[INFO] Simulation started")

        # Run backend simulation
        try:
            grid_spacing = self.graphicsViewSandbox.grid_spacing
            result = self.backend_simulator.run_simulation(self.scene, grid_spacing)

            output_lines = ["=== PySpice Simulation Results ===", ""]

            if result['success']:
                # Display results using HTML formatting for clickable node names
                html_lines = ["<pre style='font-family: monospace; font-size: 12px;'>"]
                html_lines.append("=== PySpice Simulation Results ===\n")
                html_lines.append("Simulation completed successfully!\n")
                html_lines.append("\n=== Node Voltages ===")

                for node_name, voltage_array in result['results'].items():
                    voltage = float(voltage_array[0]) if len(voltage_array) > 0 else 0.0
                    # Make node name clickable with HTML link
                    clickable_node = f"<a href='node:{node_name}' style='color: #0066cc; text-decoration: none;'>{node_name}</a>"
                    html_lines.append(f"\n  {clickable_node}: {voltage:.6f} V")

                html_lines.append("\n")

                # Show simplified circuit grid (optional)
                if 'circuit_grid' in result:
                    html_lines.append("\n=== Circuit Analysis ===")
                    html_lines.append(f"\nComponents analyzed: {len(result['circuit_grid'])}")

                html_lines.append("</pre>")

                if self.sim_output_panel:
                    self.sim_output_panel.set_output("".join(html_lines), is_html=True)

                self.log_panel.log_message("[INFO] Simulation completed successfully")
                return  # Early return to skip the standard text output at the end

            else:
                # Error handling
                output_lines.append("Simulation failed!")
                output_lines.append("")
                output_lines.append(f"Error: {result.get('error', 'Unknown error')}")

                if result.get('error_type'):
                    output_lines.append(f"Error Type: {result['error_type']}")

                if result.get('details'):
                    output_lines.append("")
                    output_lines.append("Details:")
                    output_lines.append(result['details'])

                # Special handling for PySpice not installed
                if result.get('error_type') == 'ImportError':
                    output_lines.append("")
                    output_lines.append("PySpice is not installed. To install it, run:")
                    output_lines.append("  pip install PySpice")
                    output_lines.append("")
                    output_lines.append("Note: PySpice requires ngspice to be installed on your system.")

                # Show traceback if available
                if result.get('traceback'):
                    output_lines.append("")
                    output_lines.append("=== Traceback ===")
                    output_lines.append(result['traceback'])

                # Show debug data if available
                if result.get('debug_data'):
                    debug_data = result['debug_data']
                    output_lines.append("")
                    output_lines.append("=== Debug Information ===")

                    if 'original_grid' in debug_data:
                        output_lines.append("")
                        output_lines.append("Original Circuit Grid:")
                        output_lines.append(debug_data['original_grid'])

                    if 'transformed_grid' in debug_data:
                        output_lines.append("")
                        output_lines.append("Transformed Circuit Grid:")
                        output_lines.append(debug_data['transformed_grid'])

                    if 'netlist' in debug_data:
                        output_lines.append("")
                        output_lines.append("Generated Netlist:")
                        output_lines.append(debug_data['netlist'])

                self.log_panel.log_message(f"[ERROR] {result.get('error', 'Simulation failed')}")

            simulation_result = "\n".join(output_lines)

            if self.sim_output_panel:
                self.sim_output_panel.set_output(simulation_result)

        except Exception as e:
            import traceback
            error_msg = f"Unexpected error during simulation: {e}"
            self.log_panel.log_message(f"[ERROR] {error_msg}")

            output_lines = ["=== Simulation Error ===", ""]
            output_lines.append(error_msg)
            output_lines.append("")
            output_lines.append("=== Traceback ===")
            output_lines.append(traceback.format_exc())

            if self.sim_output_panel:
                self.sim_output_panel.set_output("\n".join(output_lines))

    def on_stop(self):
        self.log_panel.log_message("[INFO] Simulation stopped")

    def on_zoom_in(self):
        self.graphicsViewSandbox.scale(1.2, 1.2)

    def on_zoom_out(self):
        self.graphicsViewSandbox.scale(0.8, 0.8)

    def on_zoom_reset(self):
        """Reset zoom to 1:1"""
        self.graphicsViewSandbox.resetTransform()
        # Enforce min zoom and clamp to grid after reset
        if hasattr(self.graphicsViewSandbox, 'update_min_zoom'):
            self.graphicsViewSandbox.update_min_zoom()
        if hasattr(self.graphicsViewSandbox, 'clamp_view_to_visual_grid'):
            self.graphicsViewSandbox.clamp_view_to_visual_grid()

    def on_center_view(self):
        """Center the view on the scene"""
        self.graphicsViewSandbox.centerOn(0, 0)
        self.log_panel.log_message("[INFO] View centered")

    def on_probe(self):
        self.log_panel.log_message("[INFO] Probe activated")

    def on_copy(self):
        """Copy selected components to clipboard"""
        selected_items = self.scene.selectedItems()
        components_data = []

        for item in selected_items:
            if hasattr(item, 'component_type'):
                # Store component data
                components_data.append({
                    "type": item.component_type,
                    "name": getattr(item, 'name', item.component_type),
                    "value": getattr(item, 'value', ''),
                    "orientation": getattr(item, 'orientation', 0),
                    "size_w": getattr(item, 'size_w', 1),
                    "size_h": getattr(item, 'size_h', 1),
                    "relative_pos": {"x": item.x(), "y": item.y()}
                })

        if components_data:
            self.clipboard_data = components_data
            self.log_panel.log_message(f"[INFO] Copied {len(components_data)} component(s)")
        else:
            self.log_panel.log_message("[INFO] No components selected to copy")

    def on_paste(self):
        """Paste components from clipboard"""
        if not self.clipboard_data:
            self.log_panel.log_message("[INFO] Clipboard is empty")
            return

        # Calculate offset for pasted components (slight offset from originals)
        offset_x = 40  # 1 grid cell
        offset_y = 40

        pasted_count = 0
        for comp_data in self.clipboard_data:
            try:
                # Create new component
                component = ComponentItem(
                    comp_data["type"],
                    comp_data["size_w"],
                    comp_data["size_h"],
                    self.graphicsViewSandbox.grid_spacing
                )

                # Set properties
                component.name = comp_data["name"] + "_copy"
                component.value = comp_data["value"]
                component.orientation = comp_data["orientation"]

                # Set position with offset
                new_x = comp_data["relative_pos"]["x"] + offset_x
                new_y = comp_data["relative_pos"]["y"] + offset_y
                component.setPos(new_x, new_y)

                # Apply rotation
                if component.orientation:
                    component.rotate_component(0)  # Triggers recreation with orientation

                # Add to scene
                self.scene.addItem(component)
                component.snap_to_grid()

                pasted_count += 1

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Failed to paste component: {e}")

        if pasted_count > 0:
            self.log_panel.log_message(f"[INFO] Pasted {pasted_count} component(s)")

    def on_copy_output_clicked(self):
        """Copy simulation output to clipboard"""
        from PyQt6.QtWidgets import QApplication

        output_text = self.sim_output_panel.get_output_text() if self.sim_output_panel else ""
        if output_text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(output_text)
            self.log_panel.log_message("[INFO] Simulatie output gekopieerd naar clipboard")
        else:
            self.log_panel.log_message("[INFO] Geen simulatie output om te kopiëren")

    def on_select_all(self):
        """Select all items in the scene"""
        for item in self.scene.items():
            if hasattr(item, 'setSelected'):
                item.setSelected(True)
        self.log_panel.log_message("[INFO] All items selected")

    def on_deselect_all(self):
        """Deselect all items"""
        self.scene.clearSelection()
        self.selected_component = None
        self.inspect_panel.show_default_state()
        self.log_panel.log_message("[INFO] Selection cleared")

    def on_focus_canvas(self):
        """Set focus to the canvas"""
        self.graphicsViewSandbox.setFocus()
        self.log_panel.log_message("[INFO] Canvas focused")

    def on_clear_log(self):
        """Clear the log"""
        self.log_panel.clear_log()

    def on_export_png(self):
        """Export circuit canvas as PNG image"""
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import QRectF

        # Ask user for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PNG",
            os.path.expanduser("~/Downloads/circuit.png"),
            "PNG Images (*.png);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Ensure .png extension
            if not file_path.endswith('.png'):
                file_path += '.png'

            # Get scene bounds
            scene_rect = self.scene.sceneRect()

            # Create high-resolution image (2x for quality)
            scale_factor = 2.0
            img_width = int(scene_rect.width() * scale_factor)
            img_height = int(scene_rect.height() * scale_factor)

            image = QImage(img_width, img_height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)

            # Render scene to image
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # Let Qt handle the scaling by specifying target and source rectangles
            target_rect = QRectF(0, 0, img_width, img_height)
            self.scene.render(painter, target_rect, scene_rect)
            painter.end()

            # Save to file
            image.save(file_path, "PNG")

            self.log_panel.log_message(f"[INFO] Circuit exported to: {os.path.basename(file_path)}")
            QMessageBox.information(
                self,
                "Exported",
                f"Circuit successfully exported to:\n{os.path.basename(file_path)}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting PNG: {e}")
            self.log_panel.log_message(f"[ERROR] Error exporting PNG: {e}")

    def on_inspect_field_changed(self):
        """Handle changes in inspect panel fields"""
        if self.selected_component and hasattr(self.selected_component, 'component_type'):
            # Update component properties based on inspect panel values
            if hasattr(self.inspect_panel, 'editName') and self.inspect_panel.editName.isVisible():
                self.selected_component.name = self.inspect_panel.editName.text()

            # Handle orientation changes from the dropdown
            if hasattr(self.inspect_panel, 'comboOrient') and self.inspect_panel.comboOrient.isVisible():
                current_orientation_text = self.inspect_panel.comboOrient.currentText()
                new_orientation = int(current_orientation_text.replace("°", ""))

                # Only rotate if orientation actually changed
                if new_orientation != self.selected_component.orientation:
                    # Calculate the rotation difference
                    rotation_diff = new_orientation - self.selected_component.orientation

                    # Handle wrapping (e.g., from 270° to 0°)
                    if rotation_diff > 180:
                        rotation_diff -= 360
                    elif rotation_diff < -180:
                        rotation_diff += 360

                    # Apply the rotation
                    self.selected_component.rotate_component(rotation_diff)

            # Update component-specific values
            comp_type = self.selected_component.component_type
            if comp_type == "Resistor" and hasattr(self.inspect_panel, 'editResistance'):
                if self.inspect_panel.editResistance.isVisible():
                    self.selected_component.value = self.inspect_panel.editResistance.text()
            elif comp_type == "Vdc" and hasattr(self.inspect_panel, 'editVoltage'):
                if self.inspect_panel.editVoltage.isVisible():
                    self.selected_component.value = self.inspect_panel.editVoltage.text()
            elif comp_type == "Switch" and hasattr(self.inspect_panel, 'comboSwitchState'):
                if self.inspect_panel.comboSwitchState.isVisible():
                    self.selected_component.value = self.inspect_panel.comboSwitchState.currentText()
            elif comp_type == "Light" and hasattr(self.inspect_panel, 'labelLightStateValue'):
                # Light state is read-only, determined by circuit simulation
                pass

    # Connection and selection handlers
    def on_connection_point_clicked(self, connection_point):
        """Handle click on a connection point with validation (no out->out)."""
        self.log_panel.log_message(f"[INFO] Connection point {connection_point.point_id} clicked")
        connection_point.highlight(True)

        # Deselect previously highlighted last point if different
        if hasattr(self, 'last_selected_point') and self.last_selected_point != connection_point:
            self.last_selected_point.highlight(False)
        self.last_selected_point = connection_point

        # If this is the first point, store and wait for second
        if not hasattr(self, 'first_selected_point'):
            self.first_selected_point = connection_point
            return

        # If same point clicked twice, reset
        if self.first_selected_point == connection_point:
            connection_point.highlight(False)
            del self.first_selected_point
            del self.last_selected_point
            return

        # Validate connection
        a = self.first_selected_point
        b = connection_point
        if not self.is_connection_allowed(a, b):
            # Invalid connection: show warning, reset highlights
            a.highlight(False)
            b.highlight(False)
            if hasattr(self, 'log_panel'):
                # Determine specific error message
                pid_a = getattr(a, 'point_id', '')
                pid_b = getattr(b, 'point_id', '')
                parent_a = getattr(a, 'parent_component', None)
                parent_b = getattr(b, 'parent_component', None)

                if parent_a is not None and parent_b is not None and parent_a is parent_b:
                    self.log_panel.log_message("[WARN] Invalid connection: cannot connect a component to itself")
                elif pid_a == 'out' and pid_b == 'out':
                    self.log_panel.log_message("[WARN] Invalid connection: out -> out is not allowed")
                else:
                    self.log_panel.log_message("[WARN] Invalid connection")
            del self.first_selected_point
            del self.last_selected_point
            return

        # Create wire if valid (use undo command)
        wire = Wire(a, b)
        command = AddWireCommand(self.scene, wire, a, b, f"Connect Wire")
        self.undo_stack.push(command)

        a.highlight(False)
        b.highlight(False)
        if hasattr(self, 'log_panel'):
            self.log_panel.log_message("[INFO] Wire connected")

        del self.first_selected_point
        del self.last_selected_point

    def on_junction_point_clicked(self, junction_point):
        """Handle click on a junction point"""
        self.log_panel.log_message(f"[INFO] Junction point clicked")
        junction_point.highlight(True)

        if hasattr(self, 'last_selected_point') and self.last_selected_point != junction_point:
            self.last_selected_point.highlight(False)

        self.last_selected_point = junction_point

        if hasattr(self, 'first_selected_point'):
            if self.first_selected_point != junction_point:
                wire = Wire(self.first_selected_point, junction_point)
                command = AddWireCommand(self.scene, wire, self.first_selected_point, junction_point, "Connect Wire")
                self.undo_stack.push(command)

                self.first_selected_point.highlight(False)
                junction_point.highlight(False)

                del self.first_selected_point
                del self.last_selected_point

                self.log_panel.log_message("[INFO] Wire connected via junction point")
        else:
            self.first_selected_point = junction_point

    def on_wire_selected(self, wire):
        """Handle wire selection"""
        self.log_panel.log_message("[INFO] Wire selected")
        self.inspect_panel.update_wire_data(wire)

    def check_position_conflict(self, component):
        """Return True if another component already occupies any grid cell of this component's footprint."""
        if not hasattr(component, 'get_occupied_grid_cells'):
            return False
        footprint = component.get_occupied_grid_cells()
        for item in self.scene.items():
            if item is component:
                continue
            if hasattr(item, 'get_occupied_grid_cells'):
                other_cells = item.get_occupied_grid_cells()
                if footprint & other_cells:
                    return True
        return False

    def find_free_grid_position(self, start_gpos, new_component):
        """Find nearest anchor grid (gx, gy) so that the entire footprint (occupied cells)
        does not overlap with existing components. Uses spiral search outwards from start.
        start_gpos: (gx, gy) anchor grid coordinate (as per get_display_grid_position()).
        Returns (gx, gy) or None if no free position found within bounds.
        """
        if not hasattr(new_component, 'get_occupied_grid_cells') or not hasattr(new_component, 'compute_effective_cell_dimensions'):
            return None
        if not hasattr(self.graphicsViewSandbox, 'grid_rect') or not self.graphicsViewSandbox.grid_rect:
            return None
        g_left, g_top, g_w, g_h = self.graphicsViewSandbox.grid_rect
        g = self.graphicsViewSandbox.grid_spacing
        # Convert scene coords to grid index range (using round consistent with snapping centers)
        min_gx = int(round(g_left / g))
        max_gx = int(round((g_left + g_w) / g))
        min_gy = int(round(g_top / g))
        max_gy = int(round((g_top + g_h) / g))

        # Build occupied cell set of existing components
        occupied = set()
        for item in self.scene.items():
            if item is new_component:
                continue
            if hasattr(item, 'get_occupied_grid_cells'):
                occupied |= item.get_occupied_grid_cells()

        start_x, start_y = start_gpos
        eff_w, eff_h = new_component.compute_effective_cell_dimensions()

        def footprint_free(ax, ay):
            # Construct footprint at anchor (ax, ay)
            cells = new_component.get_occupied_grid_cells(base_gx=ax, base_gy=ay)
            # Boundaries: ensure each cell lies within grid index rectangle
            for cx, cy in cells:
                if cx < min_gx or cx > max_gx or cy < min_gy or cy > max_gy:
                    return False
            # Overlap check
            return not (cells & occupied)

        # Test start first
        if footprint_free(start_x, start_y):
            return start_x, start_y

        # Spiral search
        for radius in range(1, 40):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue  # perimeter only
                    ax = start_x + dx
                    ay = start_y + dy
                    if footprint_free(ax, ay):
                        return ax, ay
        return None

    def on_component_selected(self, component):
        """Handle component selection"""
        self.selected_component = component
        self.inspect_panel.update_component_data(component)
        self.log_panel.log_message(f"[INFO] {component.component_type} geselecteerd")

        conflict = self.check_position_conflict(component)
        if conflict and hasattr(self, 'log_panel'):
            self.log_panel.log_message(f"[WARN] Position {component.get_display_grid_position()} already occupied")

    def delete_selected_components(self):
        """Delete selected components from the scene (with undo support)"""
        from components.connection_points import ConnectionPoint
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return

        # Collect items and their connected wires for undo
        items_data = []

        for item in selected_items:
            # Skip direct deletion of raw connection points (they are owned by components)
            if isinstance(item, ConnectionPoint):
                continue

            connected_wires = []

            # Collect connected wires for junction points
            if isinstance(item, JunctionPoint):
                connected_wires = list(getattr(item, 'connected_wires', []))

            # Collect connected wires for components
            elif hasattr(item, 'connection_points'):
                for cp in item.connection_points:
                    if hasattr(cp, 'connected_wires'):
                        connected_wires.extend(cp.connected_wires.copy())

            items_data.append((item, connected_wires))

        if items_data:
            # Create and execute multi-delete command
            command = MultiDeleteCommand(self.scene, items_data, f"Delete {len(items_data)} item(s)")
            self.undo_stack.push(command)

            self.selected_component = None
            self.inspect_panel.show_default_state()
            self.log_panel.log_message(f"[INFO] {len(items_data)} item(s) deleted")

    def refresh_all_component_connection_points(self):
        """Rebuild connection points for all components to adopt latest positioning logic."""
        for item in self.scene.items():
            if isinstance(item, ComponentItem):
                # Preserve existing wires mapping by storing wires per point_id
                saved_wires = {}
                for cp in getattr(item, 'connection_points', []):
                    if hasattr(cp, 'connected_wires'):
                        saved_wires[cp.point_id] = cp.connected_wires[:]
                item.remove_connection_points()
                item.create_connection_points()
                # Attempt to reattach wires to matching point_ids
                for cp in item.connection_points:
                    if cp.point_id in saved_wires:
                        for wire in saved_wires[cp.point_id]:
                            # Update wire endpoints if they referenced old point
                            if hasattr(wire, 'start_point') and wire.start_point.point_id == cp.point_id:
                                wire.start_point = cp
                            if hasattr(wire, 'end_point') and wire.end_point.point_id == cp.point_id:
                                wire.end_point = cp
                            cp.connected_wires.append(wire)
                            wire.update_position()
        if hasattr(self, 'log_panel'):
            self.log_panel.log_message("[INFO] Connection points refreshed for all components")

    def is_connection_allowed(self, point_a, point_b):
        """Return True if a wire may connect the two points.
        Rules:
        - Disallow out->out connections
        - Disallow connections within the same component
        """
        pid_a = getattr(point_a, 'point_id', '')
        pid_b = getattr(point_b, 'point_id', '')

        # Block out-out in either order
        if pid_a == 'out' and pid_b == 'out':
            return False

        # Block connections to the same component
        parent_a = getattr(point_a, 'parent_component', None)
        parent_b = getattr(point_b, 'parent_component', None)

        if parent_a is not None and parent_b is not None and parent_a is parent_b:
            return False

        return True

    def on_node_clicked(self, node_name: str):
        """Handle clicking on a node name in simulation output to select the corresponding wire"""
        self.log_panel.log_message(f"[INFO] Node clicked: {node_name}")

        # Parse the node name to find connected components
        # Node names are in format: "component1/component2" or single component like "ground1"
        if '/' in node_name:
            # Split to get the two connected components
            parts = node_name.split('/')
            if len(parts) == 2:
                comp1_name, comp2_name = parts
                # Find wires connecting these components
                wires = self._find_wires_between_components(comp1_name, comp2_name)
                if wires:
                    # Clear previous selection
                    self.scene.clearSelection()
                    # Select all wires connecting these components
                    for wire in wires:
                        wire.setSelected(True)
                    self.log_panel.log_message(f"[INFO] Selected {len(wires)} wire(s) connecting {comp1_name} and {comp2_name}")
                else:
                    self.log_panel.log_message(f"[WARN] No wire found connecting {comp1_name} and {comp2_name}")
        else:
            # Single component node (like ground)
            self.log_panel.log_message(f"[INFO] Node is single component: {node_name}")

    def _find_wires_between_components(self, comp1_name: str, comp2_name: str):
        """Find all wires connecting two components by their backend names"""
        wires = []

        # First, find the components by matching their backend names
        # Backend names are like '1', '2' for resistors, 'voltage_source', 'ground1', etc.
        comp1_items = self._find_components_by_backend_name(comp1_name)
        comp2_items = self._find_components_by_backend_name(comp2_name)

        if not comp1_items or not comp2_items:
            return wires

        # Find wires connecting any combination of these components
        for wire in self.scene.items():
            if not isinstance(wire, Wire):
                continue

            # Get the wire's endpoints
            start_point = getattr(wire, 'start_point', None)
            end_point = getattr(wire, 'end_point', None)

            if not start_point or not end_point:
                continue

            # Check if wire connects the two components (directly or via junctions)
            start_component = self._get_component_for_point(start_point)
            end_component = self._get_component_for_point(end_point)

            # Check if this wire connects our target components
            if ((start_component in comp1_items and end_component in comp2_items) or
                (start_component in comp2_items and end_component in comp1_items)):
                wires.append(wire)

        return wires

    def _find_components_by_backend_name(self, backend_name: str):
        """Find components in the scene that match a backend component name"""
        components = []

        for item in self.scene.items():
            if hasattr(item, 'component_type'):
                # Map component types to backend names
                comp_type = item.component_type

                # Check if this matches the backend name
                if backend_name == 'voltage_source' and comp_type == 'Vdc':
                    components.append(item)
                elif backend_name.startswith('ground') and comp_type == 'GND':
                    components.append(item)
                elif backend_name.isdigit() and comp_type == 'Resistor':
                    # For numbered components like '1', '2', '3' (resistors)
                    # We'd need to track which resistor is which number
                    # For now, accept all resistors as potential matches
                    components.append(item)

        return components

    def _get_component_for_point(self, point):
        """Get the component that owns a connection point or junction"""
        if isinstance(point, JunctionPoint):
            # For junctions, we need to trace through connected wires
            # For simplicity, return None and handle in wire search logic
            return None

        # For connection points, get parent component
        parent = getattr(point, 'parent_component', None)
        return parent

    def closeEvent(self, event):
        """Handle close event - prompt to save if there are unsaved changes"""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Unsaved Changes')
            msg_box.setText('Do you want to save your changes before closing?')
            msg_box.setIcon(QMessageBox.Icon.Question)

            # Add custom buttons
            save_btn = msg_box.addButton('Save', QMessageBox.ButtonRole.AcceptRole)
            dont_save_btn = msg_box.addButton("Don't Save", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg_box.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)

            msg_box.setDefaultButton(save_btn)
            msg_box.exec()

            clicked_button = msg_box.clickedButton()

            if clicked_button == save_btn:
                # Save the project
                self.on_save()

                # Check if save was successful (user might have cancelled)
                if self.has_unsaved_changes:
                    # Save failed or was cancelled, don't close
                    event.ignore()
                    return
            elif clicked_button == cancel_btn:
                # User cancelled, don't close
                event.ignore()
                return
            # If Don't Save, continue with closing

        # Persist splitter layout on close
        try:
            settings = QSettings("ECis", "CircuitDesigner")
            if hasattr(self, 'right_splitter') and self.right_splitter is not None:
                import json as _json
                settings.setValue("right_splitter_sizes", _json.dumps(self.right_splitter.sizes()))
        except Exception:
            pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
