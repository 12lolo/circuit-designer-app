import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGraphicsScene, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor, QKeySequence

from components import (
    Wire, ConnectionPoint, BendPoint, JunctionPoint,
    ComponentItem, DraggableButton, DroppableGraphicsView
)

# Import the new UI components
from ui.components_panel import ComponentsPanel
from ui.inspect_panel import InspectPanel
from ui.toolbar_manager import ToolbarManager
from ui.simulation_engine import SimulationEngine
from ui.canvas_tools import CanvasTools
from ui.log_panel import LogPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize component managers
        self.components_panel = None
        self.inspect_panel = None
        self.toolbar_manager = None
        self.simulation_engine = None
        self.canvas_tools = None
        self.log_panel = None

        # Track selected items for deletion
        self.selected_items = []
        self.selected_component = None

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

        # Main splitter (horizontal)
        self.splitterMain = QSplitter(Qt.Orientation.Horizontal)
        self.verticalLayout_central.addWidget(self.splitterMain)

        # Setup the three main sections
        self.setupComponentsSection()
        self.setupSandboxSection()
        self.setupInspectSection()

        # Setup log section
        self.setupLogSection()

        # Setup toolbar and connect signals
        self.setupToolbarAndConnections()

    def setupComponentsSection(self):
        """Setup the Components (Componenten) section"""
        self.components_panel = ComponentsPanel()
        self.splitterMain.addWidget(self.components_panel)

    def setupSandboxSection(self):
        """Setup the Sandbox (Zandbak) section"""
        from PyQt6.QtWidgets import QGroupBox

        self.groupSandbox = QGroupBox("Zandbak")
        self.splitterMain.addWidget(self.groupSandbox)

        self.horizontalLayout_sandbox = QHBoxLayout(self.groupSandbox)

        # Graphics view
        self.graphicsViewSandbox = DroppableGraphicsView(self)
        self.horizontalLayout_sandbox.addWidget(self.graphicsViewSandbox)

        # Canvas tools
        self.canvas_tools = CanvasTools()
        self.horizontalLayout_sandbox.addLayout(self.canvas_tools.get_layout())

        # Setup graphics scene
        self.scene = QGraphicsScene(self)
        self.graphicsViewSandbox.setScene(self.scene)

        # Initialize simulation engine
        self.simulation_engine = SimulationEngine(self.graphicsViewSandbox)

        # Draw grid
        self.drawGrid()

        # Connect canvas tool signals
        self.canvas_tools.zoom_in_requested.connect(self.on_zoom_in)
        self.canvas_tools.zoom_out_requested.connect(self.on_zoom_out)
        self.canvas_tools.probe_requested.connect(self.on_probe)

    def drawGrid(self):
        """Draw the grid on the graphics scene"""
        # Create a 15x15 grid with square cells
        scene_width = 1000  # Scene width
        scene_height = 600  # Scene height

        # Use the smaller dimension to ensure square cells
        min_dimension = min(scene_width, scene_height)
        grid_spacing = min_dimension / 15  # Same spacing for both directions to create squares

        # Update the grid spacing in the graphics view
        self.graphicsViewSandbox.grid_spacing = grid_spacing

        # Calculate actual grid dimensions (will be square)
        grid_width = 15 * grid_spacing
        grid_height = 15 * grid_spacing

        # Set scene rectangle
        self.scene.setSceneRect(-scene_width/2, -scene_height/2, scene_width, scene_height)

        # Create vertical lines (15 divisions with square cells)
        for i in range(16):  # 16 lines to create 15 divisions
            x = -grid_width/2 + i * grid_spacing
            self.scene.addLine(x, -grid_height/2, x, grid_height/2, QPen(QColor(220, 220, 220)))

        # Create horizontal lines (15 divisions with square cells)
        for i in range(16):  # 16 lines to create 15 divisions
            y = -grid_height/2 + i * grid_spacing
            self.scene.addLine(-grid_width/2, y, grid_width/2, y, QPen(QColor(220, 220, 220)))

    def setupInspectSection(self):
        """Setup the Inspect section"""
        self.inspect_panel = InspectPanel()
        self.splitterMain.addWidget(self.inspect_panel)

        # Connect inspect panel signals
        self.inspect_panel.field_changed.connect(self.on_inspect_field_changed)
        self.inspect_panel.copy_output_requested.connect(self.on_copy_output_clicked)

    def setupLogSection(self):
        """Setup the Log section"""
        self.log_panel = LogPanel()
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
                'Nieuw Project',
                'Weet je zeker dat je een nieuw project wilt starten? Alle niet-opgeslagen wijzigingen gaan verloren.',
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
        self.inspect_panel.clear_output()
        self.inspect_panel.show_default_state()

        self.log_panel.log_message("[INFO] Nieuw project gestart")

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

                # Add to scene
                self.scene.addItem(component)

                # Store in component map for wire reconstruction
                component_id = f"{component_type}_{pos['x']}_{pos['y']}"
                component_map[component_id] = component

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Fout bij laden component: {e}")

        # Load wires (simplified approach - just create wires between points)
        for wire_data in project_data.get("wires", []):
            try:
                # For now, create junction points at wire positions
                # In a more complete implementation, you'd reconstruct the exact wire connections
                start_pos = wire_data["start"]
                end_pos = wire_data["end"]

                # Create junction points
                start_junction = JunctionPoint(start_pos["x"], start_pos["y"])
                end_junction = JunctionPoint(end_pos["x"], end_pos["y"])

                self.scene.addItem(start_junction)
                self.scene.addItem(end_junction)

                # Create wire between junction points
                wire = Wire(start_junction, end_junction)
                self.scene.addItem(wire)

            except Exception as e:
                self.log_panel.log_message(f"[ERROR] Fout bij laden draad: {e}")

    def on_open(self):
        """Open an existing project file"""
        # Ask for confirmation if there are unsaved changes
        if self.scene.items():
            reply = QMessageBox.question(
                self,
                'Project Openen',
                'Weet je zeker dat je een project wilt openen? Alle niet-opgeslagen wijzigingen gaan verloren.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Show file dialog to select a project file
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Project Openen",
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

                self.log_panel.log_message(f"[INFO] Project geladen: {os.path.basename(file_name)}")

            except FileNotFoundError:
                QMessageBox.critical(self, "Fout", f"Bestand niet gevonden: {file_name}")
                self.log_panel.log_message(f"[ERROR] Bestand niet gevonden: {file_name}")
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Fout", f"Ongeldig JSON bestand: {e}")
                self.log_panel.log_message(f"[ERROR] Ongeldige projectbestand: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Fout", f"Fout bij openen project: {e}")
                self.log_panel.log_message(f"[ERROR] Fout bij openen project: {e}")

    def on_save(self):
        """Save the current project to a file"""
        # Show file dialog to select a location to save the project
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Project Opslaan",
            "ECis-projectsave",  # Default filename
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

                self.log_panel.log_message(f"[INFO] Project opgeslagen als: {os.path.basename(file_name)}")

                # Show success message
                QMessageBox.information(self, "Opgeslagen", f"Project succesvol opgeslagen als:\n{os.path.basename(file_name)}")

            except PermissionError:
                QMessageBox.critical(self, "Fout", f"Geen toestemming om te schrijven naar: {file_name}")
                self.log_panel.log_message(f"[ERROR] Geen schrijfrechten: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Fout", f"Fout bij opslaan project: {e}")
                self.log_panel.log_message(f"[ERROR] Fout bij opslaan project: {e}")

    def on_run(self):
        self.log_panel.log_message("[INFO] Simulatie gestart")

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
        self.inspect_panel.set_output(simulation_result)

        self.log_panel.log_message("[INFO] Simulatie voltooid")

    def on_stop(self):
        self.log_panel.log_message("[INFO] Simulatie gestopt")

    def on_zoom_in(self):
        self.graphicsViewSandbox.scale(1.2, 1.2)
        self.log_panel.log_message("[INFO] Ingezoomd")

    def on_zoom_out(self):
        self.graphicsViewSandbox.scale(0.8, 0.8)
        self.log_panel.log_message("[INFO] Uitgezoomd")

    def on_zoom_reset(self):
        """Reset zoom to 1:1"""
        self.graphicsViewSandbox.resetTransform()
        self.log_panel.log_message("[INFO] Zoom gereset")

    def on_center_view(self):
        """Center the view on the scene"""
        self.graphicsViewSandbox.centerOn(0, 0)
        self.log_panel.log_message("[INFO] View gecentreerd")

    def on_probe(self):
        self.log_panel.log_message("[INFO] Meetprobe geactiveerd")

    def on_copy_output_clicked(self):
        """Copy simulation output to clipboard"""
        from PyQt6.QtWidgets import QApplication

        output_text = self.inspect_panel.textOutput.toPlainText()
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
        self.log_panel.log_message("[INFO] Alle items geselecteerd")

    def on_deselect_all(self):
        """Deselect all items"""
        self.scene.clearSelection()
        self.selected_component = None
        self.inspect_panel.show_default_state()
        self.log_panel.log_message("[INFO] Selectie gewist")

    def on_focus_canvas(self):
        """Set focus to the canvas"""
        self.graphicsViewSandbox.setFocus()
        self.log_panel.log_message("[INFO] Canvas gefocust")

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
            if comp_type == "Weerstand" and hasattr(self.inspect_panel, 'editResistance'):
                if self.inspect_panel.editResistance.isVisible():
                    self.selected_component.value = self.inspect_panel.editResistance.text()
            elif comp_type in ["Spannings Bron", "Vdc"] and hasattr(self.inspect_panel, 'editVoltage'):
                if self.inspect_panel.editVoltage.isVisible():
                    self.selected_component.value = self.inspect_panel.editVoltage.text()
            elif comp_type == "Isrc" and hasattr(self.inspect_panel, 'editCurrent'):
                if self.inspect_panel.editCurrent.isVisible():
                    self.selected_component.value = self.inspect_panel.editCurrent.text()

    # Connection and selection handlers
    def on_connection_point_clicked(self, connection_point):
        """Handle click on a connection point"""
        self.log_panel.log_message(f"[INFO] Aansluitpunt {connection_point.point_id} aangeklikt")
        connection_point.highlight(True)

        if hasattr(self, 'last_selected_point') and self.last_selected_point != connection_point:
            self.last_selected_point.highlight(False)

        self.last_selected_point = connection_point

        if hasattr(self, 'first_selected_point'):
            if self.first_selected_point != connection_point:
                wire = Wire(self.first_selected_point, connection_point)
                self.scene.addItem(wire)

                self.first_selected_point.highlight(False)
                connection_point.highlight(False)

                del self.first_selected_point
                del self.last_selected_point

                self.log_panel.log_message("[INFO] Draad verbonden")
        else:
            self.first_selected_point = connection_point

    def on_junction_point_clicked(self, junction_point):
        """Handle click on a junction point"""
        self.log_panel.log_message(f"[INFO] Junctiepunt aangeklikt")
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

                self.log_panel.log_message("[INFO] Draad verbonden via junctiepunt")
        else:
            self.first_selected_point = junction_point

    def on_wire_selected(self, wire):
        """Handle wire selection"""
        self.log_panel.log_message("[INFO] Draad geselecteerd")
        self.inspect_panel.update_wire_data(wire)

    def on_component_selected(self, component):
        """Handle component selection"""
        self.selected_component = component
        self.inspect_panel.update_component_data(component)
        self.log_panel.log_message(f"[INFO] {component.component_type} geselecteerd")

    def delete_selected_components(self):
        """Delete selected components from the scene"""
        selected_items = self.scene.selectedItems()
        if selected_items:
            for item in selected_items:
                # Remove wires connected to components
                if hasattr(item, 'connection_points'):
                    for cp in item.connection_points:
                        if hasattr(cp, 'connected_wires'):
                            for wire in cp.connected_wires.copy():
                                self.scene.removeItem(wire)

                self.scene.removeItem(item)

            self.selected_component = None
            self.inspect_panel.show_default_state()
            self.log_panel.log_message(f"[INFO] {len(selected_items)} item(s) verwijderd")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
