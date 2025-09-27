from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QPlainTextEdit
from PyQt6.QtCore import pyqtSignal


class LogPanel(QGroupBox):
    """Panel for displaying application logs"""

    def __init__(self):
        super().__init__("Log")
        self.setupUi()

    def setupUi(self):
        """Setup the log panel UI"""
        self.verticalLayout_log = QVBoxLayout(self)

        self.textLog = QPlainTextEdit()
        self.textLog.setReadOnly(True)
        self.textLog.setPlainText(
            "[INFO] Simulatie gereed — 3 knooppunten, 2 componenten\n"
            "[INFO] Simulatie gestopt"
        )
        self.verticalLayout_log.addWidget(self.textLog)

    def log_message(self, message):
        """Add a message to the log"""
        self.textLog.appendPlainText(message)

    def clear_log(self):
        """Clear all log messages"""
        self.textLog.clear()

    def get_log_text(self):
        """Get all log text"""
        return self.textLog.toPlainText()
