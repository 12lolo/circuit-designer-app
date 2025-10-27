from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QSizePolicy, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QUrl


class SimulationOutputPanel(QGroupBox):
    """Standalone panel to display simulation output with copy functionality."""

    copy_output_requested = pyqtSignal()
    node_clicked = pyqtSignal(str)  # Signal emitted when a node name is clicked

    def __init__(self):
        super().__init__("Simulation Output")
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("SimulationOutputPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.label = QLabel("Simulation Output")
        self.label.setStyleSheet("font-weight: bold;")

        self.textOutput = QTextBrowser()
        self.textOutput.setReadOnly(True)
        self.textOutput.setPlaceholderText("Simulation results will appear here...")
        self.textOutput.setFrameShape(QFrame.Shape.NoFrame)
        self.textOutput.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.textOutput.setMinimumHeight(80)
        self.textOutput.setOpenLinks(False)  # Prevent default link opening behavior
        self.textOutput.anchorClicked.connect(self._on_anchor_clicked)  # Connect link click handler

        self.btnCopyOutput = QPushButton("Copy Output")
        self.btnCopyOutput.setToolTip("Copy simulation output to clipboard")
        self.btnCopyOutput.clicked.connect(self.copy_output_requested.emit)

        layout.addWidget(self.label)
        layout.addWidget(self.textOutput, 1)
        layout.addWidget(self.btnCopyOutput, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        # Light style for compactness
        self.setStyleSheet(
            """
            #SimulationOutputPanel QLabel { margin: 0; padding: 0; }
            #SimulationOutputPanel QTextBrowser { margin: 2px 0 0 0; padding: 2px; font-size: 12px; }
            #SimulationOutputPanel QPushButton { margin: 2px 0 0 0; padding: 2px 6px; font-size: 12px; }
            """
        )

    def _on_anchor_clicked(self, url: QUrl):
        """Handle clicks on node name links"""
        node_name = url.toString()
        if node_name.startswith('node:'):
            # Extract the actual node name (e.g., "node:1/voltage_source" -> "1/voltage_source")
            actual_node = node_name[5:]  # Remove "node:" prefix
            self.node_clicked.emit(actual_node)

    # Helpers
    def clear_output(self):
        self.textOutput.clear()

    def set_output(self, text: str, is_html: bool = False):
        """Set output text. If is_html is True, text is treated as HTML."""
        if is_html:
            self.textOutput.setHtml(text or "")
        else:
            self.textOutput.setPlainText(text or "")

    def get_output_text(self) -> str:
        return self.textOutput.toPlainText()

