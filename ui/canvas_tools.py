from PyQt6.QtWidgets import (
    QVBoxLayout, QToolButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import QObject, pyqtSignal


class CanvasTools(QObject):
    """Manages canvas interaction tools like zoom and probe"""

    # Signals for tool actions
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    probe_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = None
        self.setup_tools()

    def setup_tools(self):
        """Setup the canvas tools layout and buttons"""
        self.layout = QVBoxLayout()

        # Tool buttons
        self.btnZoomIn = QToolButton()
        self.btnZoomIn.setText("+")
        self.btnZoomIn.setToolTip("Zoom in")
        self.btnZoomIn.clicked.connect(self.zoom_in_requested.emit)

        self.btnZoomOut = QToolButton()
        self.btnZoomOut.setText("-")
        self.btnZoomOut.setToolTip("Zoom out")
        self.btnZoomOut.clicked.connect(self.zoom_out_requested.emit)

        self.btnProbe = QToolButton()
        self.btnProbe.setText("→")
        self.btnProbe.setToolTip("Probe")
        self.btnProbe.clicked.connect(self.probe_requested.emit)

        # Add buttons to layout
        self.layout.addWidget(self.btnZoomIn)
        self.layout.addWidget(self.btnZoomOut)
        self.layout.addWidget(self.btnProbe)

        # Add spacer
        self.verticalSpacer_canvasTools = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.layout.addItem(self.verticalSpacer_canvasTools)

    def get_layout(self):
        """Get the layout containing all canvas tools"""
        return self.layout

    def add_tool(self, text, tooltip, callback):
        """Add a custom tool button"""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)

        # Insert before the spacer (last item)
        self.layout.insertWidget(self.layout.count() - 1, button)
        return button
