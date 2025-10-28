from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from ui.value_input_widget import ValueInputWidget


class InspectPanel(QGroupBox):
    """Panel for inspecting and editing component properties"""

    # Signals
    field_changed = pyqtSignal()

    def __init__(self):
        super().__init__("Inspect")
        self.selected_component = None
        self.setupUi()

    def setupUi(self):
        """Setup the inspect panel UI"""
        self.setObjectName("InspectPanel")
        self.formLayout_inspect = QFormLayout(self)
        self.formLayout_inspect.setContentsMargins(6, 6, 6, 6)
        self.formLayout_inspect.setHorizontalSpacing(4)
        self.formLayout_inspect.setVerticalSpacing(2)

        # Build UI
        self.createDefaultElements()
        self.createCommonFields()
        self.createComponentSpecificFields()
        self.createWireFields()

        # Compact pass
        self.apply_compact_layout()

        # Default state
        self.show_default_state()

    def apply_compact_layout(self):
        """Make the inspect panel dense and top-aligned."""
        fl = self.formLayout_inspect

        # Layout spacings/packing
        fl.setContentsMargins(4, 4, 4, 4)
        fl.setHorizontalSpacing(4)
        fl.setVerticalSpacing(0)
        fl.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        fl.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fl.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Prevent vertical expansion of row widgets
        fixed_h = 20
        for w in self.findChildren((QLabel, QLineEdit, QComboBox, QPushButton, ValueInputWidget)):
            w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            w.setMinimumHeight(fixed_h)
            w.setMaximumHeight(fixed_h)

        # Value labels fixed-height as well (prevents tall rows)
        for name in ("labelTypeValue", "labelPositionValue", "labelNetIdValue",
                     "labelWireLengthValue", "labelBendPointsValue",
                     "labelWireEndpointsValue"):
            if hasattr(self, name):
                w = getattr(self, name)
                w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
                w.setMinimumHeight(fixed_h)
                w.setMaximumHeight(fixed_h)

        # Global stylesheet trims
        self.setStyleSheet(
            """
            #InspectPanel {
                margin: 0px;
            }
            QGroupBox {
                margin-top: 12px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0px 2px 2px 2px;
                margin: 0px;
            }
            #InspectPanel QLabel {
                margin: 0px;
                padding: 0px;
            }
            #InspectPanel QLineEdit,
            #InspectPanel QComboBox {
                margin: 0px;
                padding: 1px 3px;
                font-size: 12px;
            }
            #InspectPanel QPlainTextEdit {
                margin: 2px 0 0 0;
                padding: 2px;
                font-size: 12px;
            }
            #InspectPanel QPushButton {
                margin: 2px 0 0 0;
                padding: 2px 6px;
                font-size: 12px;
            }
            """
        )

    # ----- UI sections

    def createDefaultElements(self):
        self.labelDefaultInfo = QLabel("Select a component to view its properties")
        self.labelDefaultInfo.setStyleSheet("color: gray; font-style: italic;")
        self.labelDefaultInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_inspect.addRow(self.labelDefaultInfo)

    def createCommonFields(self):
        # Name
        self.labelName = QLabel("Name")
        self.editName = QLineEdit()
        self.editName.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelName, self.editName)

        # Type
        self.labelType = QLabel("Type")
        self.labelTypeValue = QLabel("--")
        self.labelTypeValue.setStyleSheet("font-weight: bold;")
        self.formLayout_inspect.addRow(self.labelType, self.labelTypeValue)

        # Position
        self.labelPosition = QLabel("Position")
        self.labelPositionValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelPosition, self.labelPositionValue)

        # Net ID (read-only)
        self.labelNetId = QLabel("Net ID")
        self.labelNetIdValue = QLabel("--")
        self.labelNetIdValue.setStyleSheet("font-family: monospace; color: #0066cc;")
        self.labelNetIdValue.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.formLayout_inspect.addRow(self.labelNetId, self.labelNetIdValue)

    def createComponentSpecificFields(self):
        # Resistance
        self.labelResistance = QLabel("Resistance")
        self.editResistance = ValueInputWidget(unit="Ω")
        self.editResistance.setPlaceholderText("e.g., 1Ω, 470Ω, 1000Ω")
        self.editResistance.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelResistance, self.editResistance)

        # Voltage
        self.labelVoltage = QLabel("Voltage")
        self.editVoltage = ValueInputWidget(unit="V")
        self.editVoltage.setPlaceholderText("e.g., 5V, 12V")
        self.editVoltage.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelVoltage, self.editVoltage)

        # Switch State
        self.labelSwitchState = QLabel("State")
        self.comboSwitchState = QComboBox()
        self.comboSwitchState.addItems(["Open", "Closed"])
        self.comboSwitchState.currentTextChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelSwitchState, self.comboSwitchState)

        # LED State
        self.labelLEDState = QLabel("State")
        self.labelLEDStateValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelLEDState, self.labelLEDStateValue)

        # LED Threshold Voltage
        self.labelLEDThreshold = QLabel("Threshold")
        self.editLEDThreshold = ValueInputWidget()
        self.editLEDThreshold.setPlaceholderText("e.g., 1.5V, 2V")
        self.editLEDThreshold.textChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelLEDThreshold, self.editLEDThreshold)

        # Orientation
        self.labelOrient = QLabel("Orientation")
        self.comboOrient = QComboBox()
        self.comboOrient.addItems(["0°", "90°", "180°", "270°"])
        self.comboOrient.currentTextChanged.connect(self.field_changed.emit)
        self.formLayout_inspect.addRow(self.labelOrient, self.comboOrient)

    def createWireFields(self):
        self.labelWireLength = QLabel("Wire Length")
        self.labelWireLengthValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelWireLength, self.labelWireLengthValue)

        self.labelBendPoints = QLabel("Bend Points")
        self.labelBendPointsValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelBendPoints, self.labelBendPointsValue)

        self.labelWireEndpoints = QLabel("Endpoints")
        self.labelWireEndpointsValue = QLabel("--")
        self.formLayout_inspect.addRow(self.labelWireEndpoints, self.labelWireEndpointsValue)

    # ----- Visibility

    def show_default_state(self):
        try:
            self.labelDefaultInfo.show()
            widgets_to_hide = [
                'labelName', 'editName', 'labelType', 'labelTypeValue',
                'labelPosition', 'labelPositionValue', 'labelResistance', 'editResistance',
                'labelVoltage', 'editVoltage', 'labelSwitchState', 'comboSwitchState',
                'labelLEDState', 'labelLEDStateValue', 'labelLEDThreshold', 'editLEDThreshold',
                'labelOrient', 'comboOrient', 'labelWireLength', 'labelWireLengthValue',
                'labelBendPoints', 'labelBendPointsValue', 'labelNetId', 'labelNetIdValue',
                'labelWireEndpoints', 'labelWireEndpointsValue'
            ]
            for widget_name in widgets_to_hide:
                if hasattr(self, widget_name):
                    getattr(self, widget_name).hide()
        except Exception as e:
            print(f"Error in show_default_state: {e}")

    def show_component_fields(self, component_type):
        try:
            self.labelDefaultInfo.hide()

            # Common
            self.labelName.show(); self.editName.show()
            self.labelType.show(); self.labelTypeValue.show()
            self.labelPosition.show(); self.labelPositionValue.show()

            # Hide specifics
            fields_to_hide = [
                ('labelResistance', 'editResistance'),
                ('labelVoltage', 'editVoltage'),
                ('labelSwitchState', 'comboSwitchState'),
                ('labelLEDState', 'labelLEDStateValue'),
                ('labelLEDThreshold', 'editLEDThreshold'),
                ('labelOrient', 'comboOrient'),
                ('labelWireLength', 'labelWireLengthValue'),
                ('labelBendPoints', 'labelBendPointsValue'),
                ('labelWireEndpoints', 'labelWireEndpointsValue')
            ]
            for label_name, widget_name in fields_to_hide:
                if hasattr(self, label_name): getattr(self, label_name).hide()
                if hasattr(self, widget_name): getattr(self, widget_name).hide()

            # Show by type
            if component_type in ["Weerstand", "Resistor"]:
                self.labelResistance.show(); self.editResistance.show()
                self.labelOrient.show(); self.comboOrient.show()
            elif component_type in ["Spannings Bron", "Vdc"]:
                self.labelVoltage.show(); self.editVoltage.show()
            elif component_type == "Switch":
                self.labelSwitchState.show(); self.comboSwitchState.show()
                self.labelOrient.show(); self.comboOrient.show()
            elif component_type == "LED":
                self.labelLEDState.show(); self.labelLEDStateValue.show()
                self.labelLEDThreshold.show(); self.editLEDThreshold.show()
                self.labelOrient.show(); self.comboOrient.show()

            # Net ID always
            self.labelNetId.show(); self.labelNetIdValue.show()

        except Exception as e:
            print(f"Error in show_component_fields: {e}")

    def show_wire_fields(self):
        try:
            self.labelDefaultInfo.hide()

            # Hide component fields
            component_fields = [
                'labelName', 'editName', 'labelPosition', 'labelPositionValue',
                'labelResistance', 'editResistance', 'labelVoltage', 'editVoltage',
                'labelSwitchState', 'comboSwitchState', 'labelLEDState', 'labelLEDStateValue',
                'labelLEDThreshold', 'editLEDThreshold',
                'labelOrient', 'comboOrient'
            ]
            for field_name in component_fields:
                if hasattr(self, field_name):
                    getattr(self, field_name).hide()

            # Show wire fields
            wire_fields = [
                ('labelType', 'labelTypeValue'),
                ('labelWireLength', 'labelWireLengthValue'),
                ('labelBendPoints', 'labelBendPointsValue'),
                ('labelWireEndpoints', 'labelWireEndpointsValue'),
                ('labelNetId', 'labelNetIdValue')
            ]
            for label_name, widget_name in wire_fields:
                if hasattr(self, label_name): getattr(self, label_name).show()
                if hasattr(self, widget_name): getattr(self, widget_name).show()

        except Exception as e:
            print(f"Error in show_wire_fields: {e}")

    # ----- Data updates

    def update_component_data(self, component):
        """Update the panel with component data"""
        self.selected_component = component

        if hasattr(component, 'component_type'):
            self.show_component_fields(component.component_type)
            self.labelTypeValue.setText(component.component_type)

            # Position (grid indices if available)
            if hasattr(component, 'get_display_grid_position'):
                gx, gy = component.get_display_grid_position()
                self.labelPositionValue.setText(f"({gx}, {gy})")
            else:
                pos = component.pos()
                self.labelPositionValue.setText(f"({pos.x():.0f}, {pos.y():.0f})")

            # Net ID - generate backend identifier
            # This matches the format used in backend_integration.py
            component_type = component.component_type
            net_id = f"{component_type}_{id(component) % 10000}"  # Simple unique ID
            self.labelNetIdValue.setText(net_id)

            # Common values
            if hasattr(component, 'name'):
                old_block = self.editName.blockSignals(True)
                self.editName.setText(component.name or "")
                self.editName.blockSignals(old_block)

            # Orientation if visible
            if hasattr(component, 'orientation') and self.comboOrient.isVisible():
                orientation_text = f"{component.orientation}°"
                index = self.comboOrient.findText(orientation_text)
                if index >= 0:
                    old_block = self.comboOrient.blockSignals(True)
                    self.comboOrient.setCurrentIndex(index)
                    self.comboOrient.blockSignals(old_block)

            if hasattr(component, 'value'):
                value = component.value or ""
                if component.component_type == "Resistor":
                    old_block = self.editResistance.blockSignals(True)
                    self.editResistance.setText(value)
                    self.editResistance.blockSignals(old_block)
                elif component.component_type == "Vdc":
                    old_block = self.editVoltage.blockSignals(True)
                    self.editVoltage.setText(value)
                    self.editVoltage.blockSignals(old_block)
                elif component.component_type == "Switch":
                    old_block = self.comboSwitchState.blockSignals(True)
                    index = self.comboSwitchState.findText(value)
                    if index >= 0:
                        self.comboSwitchState.setCurrentIndex(index)
                    self.comboSwitchState.blockSignals(old_block)
                elif component.component_type == "LED":
                    self.labelLEDStateValue.setText(value)
                    # Also set threshold if component has it
                    if hasattr(component, 'led_threshold'):
                        old_block = self.editLEDThreshold.blockSignals(True)
                        self.editLEDThreshold.setText(str(component.led_threshold) + "V")
                        self.editLEDThreshold.blockSignals(old_block)

    def update_wire_data(self, wire):
        """Update the panel with wire data, including endpoint grid coordinates"""
        self.show_wire_fields()
        self.labelTypeValue.setText("Wire")

        # Net ID - generate backend identifier for wire
        wire_id = f"wire_{id(wire) % 10000}"  # Simple unique ID
        self.labelNetIdValue.setText(wire_id)

        # Length
        if hasattr(wire, 'line'):
            line = wire.line()
            length = ((line.x2() - line.x1())**2 + (line.y2() - line.y1())**2)**0.5
            self.labelWireLengthValue.setText(f"{length:.1f}px")

        # Bend count
        bend_count = len(getattr(wire, 'bend_points', [])) if hasattr(wire, 'bend_points') else 0
        self.labelBendPointsValue.setText(str(bend_count))

        # Endpoints (grid coords if view provides spacing)
        try:
            if wire.scene() and wire.scene().views():
                view = wire.scene().views()[0]
                g = getattr(view, 'grid_spacing', None)
            else:
                g = None
            start_pt = getattr(wire, 'start_point', None)
            end_pt = getattr(wire, 'end_point', None)

            def fmt_point(pt):
                if not pt:
                    return "--"
                if hasattr(pt, 'get_scene_pos'):
                    pos = pt.get_scene_pos()
                else:
                    pos = pt.scenePos() if hasattr(pt, 'scenePos') else QPointF(0, 0)
                if g:
                    gx = int(round(pos.x() / g))
                    gy = int(round(pos.y() / g))
                    coord = f"({gx},{gy})"
                else:
                    coord = f"({pos.x():.0f},{pos.y():.0f})"
                pid = getattr(pt, 'point_id', '')
                if pid:
                    coord += f":{pid}"
                return coord

            start_txt = fmt_point(start_pt)
            end_txt = fmt_point(end_pt)
            self.labelWireEndpointsValue.setText(f"{start_txt} -> {end_txt}")
        except Exception:
            self.labelWireEndpointsValue.setText("--")
