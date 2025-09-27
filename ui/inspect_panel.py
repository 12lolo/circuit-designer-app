from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPlainTextEdit, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal


class InspectPanel(QGroupBox):
    """Panel for inspecting and editing component properties"""

    # Signal emitted when a field changes
    field_changed = pyqtSignal()
    copy_output_requested = pyqtSignal()

    def __init__(self):
        super().__init__("Inspect")
        self.selected_component = None
        self.setupUi()

    def setupUi(self):
        """Setup the inspect panel UI"""
        self.formLayout_inspect = QFormLayout(self)

        # Store all inspect widgets for dynamic show/hide
        self.inspect_widgets = {}

        # Create all UI elements
        self.createDefaultElements()
        self.createCommonFields()
        self.createComponentSpecificFields()
        self.createWireFields()
        self.createSimulationOutput()

        # Initially show default state
        self.show_default_state()

    def createDefaultElements(self):
        """Create default info label"""
        self.labelDefaultInfo = QLabel("Select a component to view its properties")
        self.labelDefaultInfo.setStyleSheet("color: gray; font-style: italic;")
        self.labelDefaultInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_inspect.addRow(self.labelDefaultInfo)

    def createCommonFields(self):
        """Create common fields for all components"""
        # Name field
        self.labelName = QLabel("Name")
        self.editName = QLineEdit()
        self.editName.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelName, self.editName)

        # Type field
        self.labelType = QLabel("Type")
        self.labelTypeValue = QLabel("--")
        self.labelTypeValue.setStyleSheet("font-weight: bold;")
        self.formLayout_inspect.addRow(self.labelType, self.labelTypeValue)

        # Position info (read-only)
        self.labelPosition = QLabel("Position")
        self.labelPositionValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelPosition, self.labelPositionValue)

        # Net ID field (for circuit analysis)
        self.labelNetId = QLabel("Net ID")
        self.editNetId = QLineEdit()
        self.editNetId.setPlaceholderText("Network identifier")
        self.editNetId.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelNetId, self.editNetId)

    def createComponentSpecificFields(self):
        """Create component-specific fields"""
        # Resistance field (for resistors)
        self.labelResistance = QLabel("Resistance")
        self.editResistance = QLineEdit()
        self.editResistance.setPlaceholderText("e.g., 1kΩ, 470Ω")
        self.editResistance.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelResistance, self.editResistance)

        # Voltage field (for voltage sources)
        self.labelVoltage = QLabel("Voltage")
        self.editVoltage = QLineEdit()
        self.editVoltage.setPlaceholderText("e.g., 5V, 12V")
        self.editVoltage.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelVoltage, self.editVoltage)

        # Current field (for current sources)
        self.labelCurrent = QLabel("Current")
        self.editCurrent = QLineEdit()
        self.editCurrent.setPlaceholderText("e.g., 1mA, 100mA")
        self.editCurrent.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelCurrent, self.editCurrent)

        # Orientation field (for rotatable components)
        self.labelOrient = QLabel("Orientation")
        self.comboOrient = QComboBox()
        self.comboOrient.addItems(["0°", "90°", "180°", "270°"])
        self.comboOrient.currentTextChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelOrient, self.comboOrient)

    def createWireFields(self):
        """Create wire-specific fields"""
        self.labelWireLength = QLabel("Wire Length")
        self.labelWireLengthValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelWireLength, self.labelWireLengthValue)

        self.labelBendPoints = QLabel("Bend Points")
        self.labelBendPointsValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelBendPoints, self.labelBendPointsValue)

    def createSimulationOutput(self):
        """Create simulation output section"""
        self.labelOutput = QLabel("Simulation Output")
        self.labelOutput.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.textOutput = QPlainTextEdit()
        self.textOutput.setReadOnly(True)
        self.textOutput.setPlaceholderText("Simulation results will appear here...")
        self.textOutput.setMaximumHeight(150)
        self.formLayout_inspect.addRow(self.labelOutput)
        self.formLayout_inspect.addRow(self.textOutput)

        # Copy button for simulation output
        self.btnCopyOutput = QPushButton("Copy Output")
        self.btnCopyOutput.setToolTip("Copy simulation output to clipboard")
        self.btnCopyOutput.clicked.connect(self.copy_output_requested.emit)
        self.formLayout_inspect.addRow(self.btnCopyOutput)

    def show_default_state(self):
        """Show the default inspect panel when nothing is selected"""
        try:
            # Show default info
            self.labelDefaultInfo.show()

            # Hide all other fields safely
            widgets_to_hide = [
                'labelName', 'editName', 'labelType', 'labelTypeValue',
                'labelPosition', 'labelPositionValue', 'labelResistance', 'editResistance',
                'labelVoltage', 'editVoltage', 'labelCurrent', 'editCurrent',
                'labelOrient', 'comboOrient', 'labelWireLength', 'labelWireLengthValue',
                'labelBendPoints', 'labelBendPointsValue', 'labelNetId', 'editNetId'
            ]

            for widget_name in widgets_to_hide:
                if hasattr(self, widget_name):
                    getattr(self, widget_name).hide()
        except Exception as e:
            print(f"Error in show_default_state: {e}")

    def show_component_fields(self, component_type):
        """Show inspect panel fields appropriate for the selected component type"""
        try:
            # Hide default info
            self.labelDefaultInfo.hide()

            # Show common fields for all components
            self.labelName.show()
            self.editName.show()
            self.labelType.show()
            self.labelTypeValue.show()
            self.labelPosition.show()
            self.labelPositionValue.show()

            # Hide all component-specific fields first
            fields_to_hide = [
                ('labelResistance', 'editResistance'),
                ('labelVoltage', 'editVoltage'),
                ('labelCurrent', 'editCurrent'),
                ('labelOrient', 'comboOrient'),
                ('labelWireLength', 'labelWireLengthValue'),
                ('labelBendPoints', 'labelBendPointsValue')
            ]

            for label_name, widget_name in fields_to_hide:
                if hasattr(self, label_name):
                    getattr(self, label_name).hide()
                if hasattr(self, widget_name):
                    getattr(self, widget_name).hide()

            # Show component-specific fields
            if component_type == "Weerstand":
                self.labelResistance.show()
                self.editResistance.show()
                self.labelOrient.show()
                self.comboOrient.show()
            elif component_type in ["Spannings Bron", "Vdc"]:
                self.labelVoltage.show()
                self.editVoltage.show()
                if component_type == "Spannings Bron":
                    self.labelOrient.show()
                    self.comboOrient.show()
            elif component_type == "Isrc":
                self.labelCurrent.show()
                self.editCurrent.show()
                self.labelOrient.show()
                self.comboOrient.show()

            # Always show Net ID for components (even GND)
            self.labelNetId.show()
            self.editNetId.show()

        except Exception as e:
            print(f"Error in show_component_fields: {e}")

    def show_wire_fields(self):
        """Show inspect panel fields appropriate for selected wires"""
        try:
            # Hide default info
            self.labelDefaultInfo.hide()

            # Hide component fields
            component_fields = [
                'labelName', 'editName', 'labelPosition', 'labelPositionValue',
                'labelResistance', 'editResistance', 'labelVoltage', 'editVoltage',
                'labelCurrent', 'editCurrent', 'labelOrient', 'comboOrient'
            ]

            for field_name in component_fields:
                if hasattr(self, field_name):
                    getattr(self, field_name).hide()

            # Show wire-specific fields
            wire_fields = [
                ('labelType', 'labelTypeValue'),
                ('labelWireLength', 'labelWireLengthValue'),
                ('labelBendPoints', 'labelBendPointsValue'),
                ('labelNetId', 'editNetId')
            ]

            for label_name, widget_name in wire_fields:
                if hasattr(self, label_name):
                    getattr(self, label_name).show()
                if hasattr(self, widget_name):
                    getattr(self, widget_name).show()

        except Exception as e:
            print(f"Error in show_wire_fields: {e}")

    def update_component_data(self, component):
        """Update the panel with component data"""
        self.selected_component = component

        if hasattr(component, 'component_type'):
            self.show_component_fields(component.component_type)
            self.labelTypeValue.setText(component.component_type)

            # Update position
            pos = component.pos()
            self.labelPositionValue.setText(f"({pos.x():.0f}, {pos.y():.0f})")

            # Update component-specific values
            if hasattr(component, 'name'):
                self.editName.setText(component.name or "")

            # Update orientation dropdown if it's visible
            if hasattr(component, 'orientation') and hasattr(self, 'comboOrient') and self.comboOrient.isVisible():
                orientation_text = f"{component.orientation}°"
                # Find and set the correct index in the dropdown
                index = self.comboOrient.findText(orientation_text)
                if index >= 0:
                    self.comboOrient.setCurrentIndex(index)

            if hasattr(component, 'value'):
                value = component.value or ""
                if component.component_type == "Weerstand":
                    self.editResistance.setText(value)
                elif component.component_type in ["Spannings Bron", "Vdc"]:
                    self.editVoltage.setText(value)
                elif component.component_type == "Isrc":
                    self.editCurrent.setText(value)

    def update_wire_data(self, wire):
        """Update the panel with wire data"""
        self.show_wire_fields()
        self.labelTypeValue.setText("Wire")

        # Calculate wire length if possible
        if hasattr(wire, 'line'):
            line = wire.line()
            length = ((line.x2() - line.x1())**2 + (line.y2() - line.y1())**2)**0.5
            self.labelWireLengthValue.setText(f"{length:.1f}px")

    def clear_output(self):
        """Clear the simulation output"""
        self.textOutput.clear()

    def set_output(self, text):
        """Set the simulation output text"""
        self.textOutput.setPlainText(text)
