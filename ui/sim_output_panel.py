from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSizePolicy, QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class SimulationOutputPanel(QGroupBox):
    """Standalone panel to display simulation output with copy functionality."""

    copy_output_requested = pyqtSignal()

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

        self.textOutput = QPlainTextEdit()
        self.textOutput.setReadOnly(True)
        self.textOutput.setPlaceholderText("Simulation results will appear here...")
        self.textOutput.setFrameShape(QFrame.Shape.NoFrame)
        self.textOutput.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.textOutput.setMinimumHeight(80)

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
            #SimulationOutputPanel QPlainTextEdit { margin: 2px 0 0 0; padding: 2px; font-size: 12px; }
            #SimulationOutputPanel QPushButton { margin: 2px 0 0 0; padding: 2px 6px; font-size: 12px; }
            """
        )

    # Helpers
    def clear_output(self):
        self.textOutput.clear()

    def set_output(self, text: str):
        self.textOutput.setPlainText(text or "")

    def get_output_text(self) -> str:
        return self.textOutput.toPlainText()

