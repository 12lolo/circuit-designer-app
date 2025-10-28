from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QScrollArea, QWidget, QSpacerItem, QSizePolicy
)
from components import DraggableButton


class ComponentsPanel(QGroupBox):
    """Panel containing draggable component buttons"""

    def __init__(self):
        super().__init__("Components")
        self.setupUi()

    def setupUi(self):
        """Setup the components panel UI"""
        self.verticalLayout_components = QVBoxLayout(self)

        # Scroll area for components
        self.scrollComponents = QScrollArea()
        self.scrollComponents.setWidgetResizable(True)
        self.verticalLayout_components.addWidget(self.scrollComponents)

        # Scroll area contents
        self.scrollAreaWidgetContents = QWidget()
        self.scrollComponents.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_buttons = QVBoxLayout(self.scrollAreaWidgetContents)

        # Create draggable component buttons with sizes (width x height in grid cells)
        self.createComponentButtons()

        # Add spacer at the bottom
        self.verticalSpacer_components = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout_buttons.addItem(self.verticalSpacer_components)

    def createComponentButtons(self):
        """Create all the draggable component buttons"""
        # Draggable component buttons with sizes (width x height in grid cells)
        self.btnResistor = DraggableButton("Resistor", "Resistor", 2, 1)  # 2x1 grid cells
        self.btnVdc = DraggableButton("Vdc", "Vdc", 1, 1)  # 1x1 grid cell
        self.btnGnd = DraggableButton("GND", "GND", 1, 1)  # 1x1 grid cell
        self.btnSwitch = DraggableButton("Switch", "Switch", 2, 1)  # 2x1 grid cells
        self.btnLED = DraggableButton("LED", "LED", 2, 1)  # 2x1 grid cells (has two terminals)

        # Add buttons to layout
        self.verticalLayout_buttons.addWidget(self.btnResistor)
        self.verticalLayout_buttons.addWidget(self.btnVdc)
        self.verticalLayout_buttons.addWidget(self.btnGnd)
        self.verticalLayout_buttons.addWidget(self.btnSwitch)
        self.verticalLayout_buttons.addWidget(self.btnLED)

    def addComponent(self, name, display_name, width, height):
        """Add a new component button to the panel"""
        button = DraggableButton(display_name, name, width, height)
        # Insert before the spacer (last item)
        self.verticalLayout_buttons.insertWidget(
            self.verticalLayout_buttons.count() - 1, button
        )
        return button
