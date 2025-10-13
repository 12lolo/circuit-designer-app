import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGraphicsScene, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QPointF, QSettings, QEvent
from PyQt6.QtGui import QPen, QColor

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
        except Exception:
            # Fallback: ignore floating controls if creation fails
            self._floating_controls = None

    def _position_floating_controls(self):
        """Place floating controls at a fixed margin inside the canvas (top-left)."""
        if self._floating_controls is None:
            return
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

        # Connect toolbar signals
        self.toolbar_manager.new_requested.connect(self.on_new)
        self.toolbar_manager.open_requested.connect(self.on_open)
        self.toolbar_manager.save_requested.connect(self.on_save)
        self.toolbar_manager.run_requested.connect(self.on_run)
        self.toolbar_manager.stop_requested.connect(self.on_stop)

        # Connect additional action signals
        self.toolbar_manager.copy_output_requested.connect(self.on_copy_output_clicked)
        self.toolbar_manager.select_all_requested.connect(self.on_select_all)
        self.toolbar_manager.deselect_all_requested.connect(self.on_deselect_all)
        self.toolbar_manager.focus_canvas_requested.connect(self.on_focus_canvas)
        self.toolbar_manager.clear_log_requested.connect(self.on_clear_log)
        self.toolbar_manager.zoom_in_requested.connect(self.on_zoom_in)
        self.toolbar_manager.zoom_out_requested.connect(self.on_zoom_out)
        self.toolbar_manager.zoom_reset_requested.connect(self.on_zoom_reset)
        self.toolbar_manager.center_view_requested.connect(self.on_center_view)
        # Removed: clear sandbox action is now in floating controls
        # self.toolbar_manager.clear_sandbox_requested.connect(self.on_clear_sandbox)

    def keyPressEvent(self, event):
        """Enhanced keyboard event handling"""
        key = event.key()
        modifiers = event.modifiers()

        # Handle component rotation for selected items
        if key == Qt.Key.Key_R and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self.selected_component and hasattr(self.selected_component, 'component_type'):
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.selected_component.rotate_component(-90)
                else:
                    self.selected_component.rotate_component(90)
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
        """Open an existing project file"""
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

        # Show file dialog to select a project file
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "ECis Project Files (*.ecis);;JSON Files (*.json);;All Files (*)"
        )

        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as json_file:
                    project_data = json.load(json_file)

                # Deserialize and load the project data
                self.deserialize_project_data(project_data)

                # Clear selection and update UI
                self.selected_component = None
                self.inspect_panel.show_default_state()

                self.log_panel.log_message(f"[INFO] Project loaded: {os.path.basename(file_name)}")

            except FileNotFoundError:
                QMessageBox.critical(self, "Error", f"File not found: {file_name}")
                self.log_panel.log_message(f"[ERROR] File not found: {file_name}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error", f"Invalid JSON file: {e}")
                self.log_panel.log_message(f"[ERROR] Invalid project file: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error opening project: {e}")
                self.log_panel.log_message(f"[ERROR] Error opening project: {e}")

    def on_save(self):
        """Save the current project to a file"""
        # Show file dialog to select a location to save the project
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "ECis-project",
            "ECis Project Files (*.ecis);;JSON Files (*.json);;All Files (*)"
        )

        if file_name:
            try:
                # Ensure proper file extension
                if not file_name.endswith(('.ecis', '.json')):
                    file_name += '.ecis'

                # Serialize the project data
                project_data = self.serialize_project_data()

                # Save to file
                with open(file_name, 'w', encoding='utf-8') as json_file:
                    json.dump(project_data, json_file, indent=2, ensure_ascii=False)

                self.log_panel.log_message(f"[INFO] Project saved as: {os.path.basename(file_name)}")

                # Show success message
                QMessageBox.information(self, "Saved", f"Project successfully saved as:\n{os.path.basename(file_name)}")

            except PermissionError:
                QMessageBox.critical(self, "Error", f"No permission to write to: {file_name}")
                self.log_panel.log_message(f"[ERROR] No write permissions: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving project: {e}")
                self.log_panel.log_message(f"[ERROR] Error saving project: {e}")

    def on_run(self):
        self.log_panel.log_message("[INFO] Simulation started")

        # Get all components from the scene
        components = []
        wires = []

        for item in self.scene.items():
            if hasattr(item, 'component_type'):
                components.append(item)
            elif isinstance(item, Wire):  # Only count actual Wire objects
                wires.append(item)

        # Simulate the circuit using the simulation engine
        simulation_result = self.simulation_engine.simulate_circuit(components, wires)
        if self.sim_output_panel:
            self.sim_output_panel.set_output(simulation_result)

        self.log_panel.log_message("[INFO] Simulation finished")

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
            elif comp_type in ["Voltage Source", "Vdc"] and hasattr(self.inspect_panel, 'editVoltage'):
                if self.inspect_panel.editVoltage.isVisible():
                    self.selected_component.value = self.inspect_panel.editVoltage.text()
            elif comp_type == "Current Source" and hasattr(self.inspect_panel, 'editCurrent'):
                if self.inspect_panel.editCurrent.isVisible():
                    self.selected_component.value = self.inspect_panel.editCurrent.text()

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
                self.log_panel.log_message("[WARN] Invalid connection: out -> out is not allowed")
            del self.first_selected_point
            del self.last_selected_point
            return

        # Create wire if valid
        wire = Wire(a, b)
        self.scene.addItem(wire)
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
                self.scene.addItem(wire)

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
        """Delete selected components from the scene"""
        from components.connection_points import ConnectionPoint
        selected_items = self.scene.selectedItems()
        if selected_items:
            removed_count = 0
            for item in selected_items:
                # Skip direct deletion of raw connection points (they are owned by components)
                if isinstance(item, ConnectionPoint):
                    continue
                # If it's a junction point, remove its connected wires first using proper cleanup
                if isinstance(item, JunctionPoint):
                    try:
                        for wire in list(getattr(item, 'connected_wires', [])):
                            if hasattr(wire, 'delete_wire'):
                                wire.delete_wire()
                            elif wire.scene():
                                self.scene.removeItem(wire)
                    except Exception:
                        pass
                # Remove wires connected to components
                if hasattr(item, 'connection_points'):
                    for cp in item.connection_points:
                        if hasattr(cp, 'connected_wires'):
                            for wire in cp.connected_wires.copy():
                                if hasattr(wire, 'delete_wire'):
                                    wire.delete_wire()
                                elif wire.scene():
                                    self.scene.removeItem(wire)
                # Finally remove the item itself (component, wire segment group, or junction)
                self.scene.removeItem(item)
                removed_count += 1
            self.selected_component = None
            self.inspect_panel.show_default_state()
            self.log_panel.log_message(f"[INFO] {removed_count} item(s) removed (excluding protected connection points)")

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
        Current rule: disallow out->out. Future rules can be added here."""
        pid_a = getattr(point_a, 'point_id', '')
        pid_b = getattr(point_b, 'point_id', '')
        # Block out-out in either order
        if pid_a == 'out' and pid_b == 'out':
            return False
        return True

    def closeEvent(self, event):
        """Persist splitter layout on close and pass event to base class."""
        try:
            settings = QSettings("ECis", "CircuitDesigner")
            if hasattr(self, 'right_splitter') and self.right_splitter is not None:
                import json as _json
                settings.setValue("right_splitter_sizes", _json.dumps(self.right_splitter.sizes()))
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
