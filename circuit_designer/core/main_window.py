import sys
import json
import os
import traceback
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGraphicsScene, QMessageBox, QFileDialog, QDialog, QGroupBox, QGraphicsRectItem, QInputDialog
)
from PyQt6.QtCore import Qt, QPointF, QSettings, QEvent, QTimer, QRectF
from PyQt6.QtGui import QPen, QColor, QUndoStack, QBrush, QImage, QPainter

from circuit_designer.components import (
    Wire, ComponentItem, DroppableGraphicsView
)
from circuit_designer.components.connection_points import ConnectionPoint

# Import the new UI components
from circuit_designer.ui.panels.components_panel import ComponentsPanel
from circuit_designer.ui.panels.inspect_panel import InspectPanel
from circuit_designer.ui.managers.toolbar_manager import ToolbarManager
from circuit_designer.simulation.simulation_engine import SimulationEngine
from circuit_designer.utils.canvas_tools import CanvasTools
from circuit_designer.ui.panels.log_panel import LogPanel
from circuit_designer.ui.panels.sim_output_panel import SimulationOutputPanel
from circuit_designer.project.project_manager import ProjectManager
from circuit_designer.ui.panels.project_browser import ProjectBrowserDialog
from circuit_designer.simulation.netlist_builder import NetlistBuilder
from circuit_designer.ui.dialogs.shortcuts_dialog import ShortcutsDialog
from circuit_designer.project.undo_commands import (
    AddComponentCommand, DeleteComponentCommand, MoveComponentCommand,
    RotateComponentCommand, AddWireCommand, DeleteWireCommand, MultiDeleteCommand
)
from circuit_designer.ui.managers.quick_access_toolbar import make_menu_pinnable
from circuit_designer.simulation.backend_integration import BackendSimulator
from circuit_designer.core.managers import (
    CanvasManager, ComponentManager, WireManager, SelectionManager
)


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

        # Store component name mapping from last simulation
        self.component_name_mapping = {}

        # Clipboard for copy/paste
        self.clipboard_data = None

        # Track unsaved changes
        self.has_unsaved_changes = False

        self.setupUi()

        # Initialize managers (after UI setup so they have access to components)
        self.canvas_manager = None
        self.component_manager = None
        self.wire_manager = None
        self.selection_manager = None
        self._initialize_managers()

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
        if hasattr(self, 'component_manager') and self.component_manager:
            self.component_manager.refresh_all_connection_points()

    def _initialize_managers(self):
        """Initialize all manager classes"""
        # Canvas manager for viewport and grid operations
        self.canvas_manager = CanvasManager(
            self.graphicsViewSandbox,
            self.scene,
            self.log_panel
        )

        # Component manager for component operations
        self.component_manager = ComponentManager(
            self.scene,
            self.graphicsViewSandbox,
            self.inspect_panel,
            self.log_panel,
            self.undo_stack,
            self.backend_simulator
        )

        # Wire manager for wire creation and connections
        self.wire_manager = WireManager(
            self.scene,
            self.inspect_panel,
            self.log_panel,
            self.undo_stack
        )

        # Selection manager for selection and copy/paste
        self.selection_manager = SelectionManager(
            self.scene,
            self.graphicsViewSandbox,
            self.inspect_panel,
            self.log_panel,
            self.undo_stack
        )

        # Draw grid now that canvas manager is initialized
        self.canvas_manager.draw_grid()

        # Set floating controls reference in canvas manager
        if self._floating_controls:
            self.canvas_manager.set_floating_controls(self._floating_controls)

    def setupComponentsSection(self):
        """Setup the Components (Componenten) section"""
        self.components_panel = ComponentsPanel()
        self.splitterMain.addWidget(self.components_panel)

    def setupSandboxSection(self):
        """Setup the Sandbox (Zandbak) section"""
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

        # Note: Grid will be drawn after managers are initialized

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
        if self.canvas_manager:
            self.canvas_manager.position_floating_controls()

    def eventFilter(self, obj, event):
        # Reposition floating controls when the canvas viewport resizes
        if obj is getattr(self.graphicsViewSandbox, 'viewport', lambda: None)() and event.type() == QEvent.Type.Resize:
            self._position_floating_controls()
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure overlay is positioned after initial show and layout
        try:
            QTimer.singleShot(0, self._position_floating_controls)
        except Exception:
            self._position_floating_controls()

    def drawGrid(self):
        """Draw the grid on the graphics scene - delegates to canvas_manager"""
        if self.canvas_manager:
            self.canvas_manager.draw_grid()

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
                sizes = json.loads(sizes_json)
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
        self.sim_output_panel.led_clicked.connect(self.on_led_clicked)

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
        sim_menu.addSeparator()
        make_menu_pinnable(sim_menu, toolbar, self.toolbar_manager.actionCopyOutput, "Copy Output")

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        shortcuts_action = settings_menu.addAction("Keyboard Shortcuts...")
        shortcuts_action.triggered.connect(self.on_show_shortcuts_dialog)


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

    def _find_connection_point_at_position(self, position, component_id, component_map):
        """Find the connection point at a given position, optionally on a specific component"""
        # If we have a component_id, try to find the connection point on that specific component
        if component_id and component_id in component_map:
            component = component_map[component_id]
            # Find the closest connection point on this component
            if hasattr(component, 'connection_points'):
                closest_point = None
                min_distance = float('inf')

                for cp in component.connection_points:
                    cp_pos = cp.get_scene_pos()
                    distance = ((cp_pos.x() - position.x())**2 + (cp_pos.y() - position.y())**2)**0.5
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = cp

                # Accept if within 20 pixels (roughly half a grid spacing)
                if closest_point and min_distance < 20:
                    return closest_point

        # Otherwise, search all items in the scene at that position
        tolerance = 10  # pixels
        for item in self.scene.items():
            # Check if it's a connection point
            if hasattr(item, 'get_scene_pos') and hasattr(item, 'connected_wires'):
                item_pos = item.get_scene_pos()
                distance = ((item_pos.x() - position.x())**2 + (item_pos.y() - position.y())**2)**0.5
                if distance < tolerance:
                    return item

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

        # Load wires - reconnect to actual component connection points
        for wire_data in project_data.get("wires", []):
            try:
                start_pos = wire_data["start"]
                end_pos = wire_data["end"]
                start_component_id = wire_data["start"].get("component_id")
                end_component_id = wire_data["end"].get("component_id")

                # Find connection points at the wire positions
                start_point = self._find_connection_point_at_position(
                    QPointF(start_pos["x"], start_pos["y"]),
                    start_component_id,
                    component_map
                )
                end_point = self._find_connection_point_at_position(
                    QPointF(end_pos["x"], end_pos["y"]),
                    end_component_id,
                    component_map
                )

                # Only create wire if both endpoints are valid
                if start_point and end_point:
                    wire = Wire(start_point, end_point)
                    self.scene.addItem(wire)
                    wire.update_position()  # Ensure wire is drawn correctly
                else:
                    self.log_panel.log_message(f"[WARN] Could not reconnect wire: endpoints not found")

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
                # Store component name mapping for node selection
                if 'component_name_mapping' in result:
                    self.component_name_mapping = result['component_name_mapping']

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

                # Update LED states based on simulation results
                led_state_changes = self._update_led_states(result)

                # Display LED state changes in output
                if led_state_changes:
                    html_lines.append("\n\n=== LED States ===")
                    for state_msg in led_state_changes:
                        html_lines.append(f"\n  {state_msg}")

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
            error_msg = f"Unexpected error during simulation: {e}"
            self.log_panel.log_message(f"[ERROR] {error_msg}")

            output_lines = ["=== Simulation Error ===", ""]
            output_lines.append(error_msg)
            output_lines.append("")
            output_lines.append("=== Traceback ===")
            output_lines.append(traceback.format_exc())

            if self.sim_output_panel:
                self.sim_output_panel.set_output("\n".join(output_lines))

    def on_zoom_in(self):
        """Zoom in on the canvas"""
        if self.canvas_manager:
            self.canvas_manager.zoom_in()

    def on_zoom_out(self):
        """Zoom out on the canvas"""
        if self.canvas_manager:
            self.canvas_manager.zoom_out()

    def on_zoom_reset(self):
        """Reset zoom to 1:1"""
        if self.canvas_manager:
            self.canvas_manager.zoom_reset()

    def on_center_view(self):
        """Center the view on the scene"""
        if self.canvas_manager:
            self.canvas_manager.center_view()

    def on_probe(self):
        self.log_panel.log_message("[INFO] Probe activated")

    def on_copy(self):
        """Copy selected components to clipboard"""
        if self.selection_manager:
            self.selection_manager.copy_selected()

    def on_paste(self):
        """Paste components from clipboard"""
        if self.selection_manager:
            self.selection_manager.paste()

    def on_copy_output_clicked(self):
        """Copy simulation output to clipboard"""
        output_text = self.sim_output_panel.get_output_text() if self.sim_output_panel else ""
        if output_text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(output_text)
            self.log_panel.log_message("[INFO] Simulation output copied to clipboard")
        else:
            self.log_panel.log_message("[INFO] No simulation output to copy")

    def on_select_all(self):
        """Select all items in the scene"""
        if self.selection_manager:
            self.selection_manager.select_all()

    def on_deselect_all(self):
        """Deselect all items"""
        if self.selection_manager:
            self.selection_manager.deselect_all()
        if self.component_manager:
            self.component_manager.clear_selection()
        if self.wire_manager:
            self.wire_manager.reset_connection_state()

    def on_focus_canvas(self):
        """Set focus to the canvas"""
        self.graphicsViewSandbox.setFocus()
        self.log_panel.log_message("[INFO] Canvas focused")

    def on_clear_log(self):
        """Clear the log"""
        self.log_panel.clear_log()

    def on_export_png(self):
        """Export circuit canvas as PNG image"""
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
        if self.component_manager:
            self.component_manager.on_inspect_field_changed()

    # Connection and selection handlers
    def on_connection_point_clicked(self, connection_point):
        """Handle click on a connection point with validation (no out->out)."""
        if self.wire_manager:
            self.wire_manager.on_connection_point_clicked(connection_point)

    def on_wire_selected(self, wire):
        """Handle wire selection"""
        if self.wire_manager:
            self.wire_manager.on_wire_selected(wire)

    def check_position_conflict(self, component):
        """Return True if another component already occupies any grid cell of this component's footprint."""
        if self.component_manager:
            return self.component_manager.check_position_conflict(component)
        return False

    def find_free_grid_position(self, start_gpos, new_component):
        """Find nearest free grid position for a component"""
        if self.component_manager:
            return self.component_manager.find_free_grid_position(start_gpos, new_component)
        return None

    def on_component_selected(self, component):
        """Handle component selection"""
        self.selected_component = component
        if self.component_manager:
            self.component_manager.on_component_selected(component)

    def delete_selected_components(self):
        """Delete selected components from the scene (with undo support)"""
        if self.selection_manager:
            deleted = self.selection_manager.delete_selected()
            if deleted:
                self.selected_component = None

    def refresh_all_component_connection_points(self):
        """Rebuild connection points for all components to adopt latest positioning logic."""
        if self.component_manager:
            self.component_manager.refresh_all_connection_points()

    def is_connection_allowed(self, point_a, point_b):
        """Return True if a wire may connect the two points."""
        if self.wire_manager:
            return self.wire_manager.is_connection_allowed(point_a, point_b)
        return False

    def _update_led_states(self, simulation_result):
        """Update LED component states based on simulation results"""
        if not simulation_result.get('success'):
            return

        results = simulation_result.get('results', {})
        component_name_mapping = simulation_result.get('component_name_mapping', {})

        # Find LED backend names
        led_backend_names = []
        for backend_name, component in component_name_mapping.items():
            if hasattr(component, 'component_type') and component.component_type == 'LED':
                led_backend_names.append((backend_name, component))

        # Store LED state changes for output (HTML formatted)
        led_state_changes = []

        # Update each LED based on voltage across it
        for backend_name, led_component in led_backend_names:
            # Try to find node voltages for this LED
            # LEDs are named like "led1", "led2", etc.
            # Look for nodes that reference this LED
            led_voltage = 0.0

            for node_name, voltage_array in results.items():
                # Node names are like "led1/2" or "1/led1"
                if backend_name in node_name:
                    voltage = float(voltage_array[0]) if len(voltage_array) > 0 else 0.0
                    led_voltage = abs(voltage)  # Use absolute value
                    break

            # Get threshold from component or use default
            voltage_threshold = getattr(led_component, 'led_threshold', 1.5)  # Default 1.5V

            old_state = led_component.value

            # Update LED state based on voltage threshold
            if led_voltage > voltage_threshold:
                led_component.value = "On"
                # Create clickable LED name for HTML output
                clickable_led = f"<a href='led:{backend_name}' style='color: #0066cc; text-decoration: none;'>{backend_name}</a>"
                state_message_html = f"LED {clickable_led} turned ON ({led_voltage:.2f}V > {voltage_threshold:.1f}V threshold)"
                state_message_plain = f"LED {backend_name} turned ON ({led_voltage:.2f}V > {voltage_threshold:.1f}V threshold)"
            else:
                led_component.value = "Off"
                # Create clickable LED name for HTML output
                clickable_led = f"<a href='led:{backend_name}' style='color: #0066cc; text-decoration: none;'>{backend_name}</a>"
                state_message_html = f"LED {clickable_led} stayed OFF ({led_voltage:.2f}V ≤ {voltage_threshold:.1f}V threshold)"
                state_message_plain = f"LED {backend_name} stayed OFF ({led_voltage:.2f}V ≤ {voltage_threshold:.1f}V threshold)"

            # Store state change for output (HTML version)
            led_state_changes.append(state_message_html)
            self.log_panel.log_message(f"[INFO] {state_message_plain}")

            # Update inspect panel if this LED is selected
            if self.selected_component is led_component:
                if hasattr(self.inspect_panel, 'update_component_data'):
                    self.inspect_panel.update_component_data(led_component)

        # Return LED state changes to be displayed in simulation output
        return led_state_changes

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

    def on_led_clicked(self, led_backend_name: str):
        """Handle clicking on an LED name in simulation output to select the corresponding LED component"""
        self.log_panel.log_message(f"[INFO] LED clicked: {led_backend_name}")

        # Find the LED component by its backend name
        if led_backend_name in self.component_name_mapping:
            led_component = self.component_name_mapping[led_backend_name]

            # Clear previous selection
            self.scene.clearSelection()

            # Select the LED component
            led_component.setSelected(True)

            # Update inspect panel to show LED details
            self.on_component_selected(led_component)

            self.log_panel.log_message(f"[INFO] Selected LED {led_backend_name}")
        else:
            self.log_panel.log_message(f"[WARN] LED {led_backend_name} not found in scene")

    def _find_wires_between_components(self, comp1_name: str, comp2_name: str):
        """Find all wires connecting two components by their backend names"""
        if self.wire_manager:
            return self.wire_manager.find_wires_between_components(
                comp1_name, comp2_name, self.component_name_mapping
            )
        return []

    def _find_components_by_backend_name(self, backend_name: str):
        """Find components in the scene that match a backend component name"""
        if self.wire_manager:
            return self.wire_manager._find_components_by_backend_name(
                backend_name, self.component_name_mapping
            )
        return []

    def _get_component_for_point(self, point):
        """Get the component that owns a connection point"""
        if self.wire_manager:
            return self.wire_manager._get_component_for_point(point)
        return None

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
                settings.setValue("right_splitter_sizes", json.dumps(self.right_splitter.sizes()))
        except Exception:
            pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
