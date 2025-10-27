"""
Custom value input widget with increment/decrement arrows and auto-formatting
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QToolButton, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import re


class ValueInputWidget(QLineEdit):
    """Input widget with up/down arrows for incrementing values"""

    # Note: We inherit textChanged signal from QLineEdit, no need to redefine it

    def __init__(self, unit="Ω", parent=None):
        super().__init__(parent)
        self.unit = unit
        self.lineEdit = self  # For compatibility with existing code
        self.setupUi()

    def setupUi(self):
        # Set placeholder
        self.setPlaceholderText(f"e.g., 1k{self.unit}, 470{self.unit}")

        # Add padding on the right to make room for arrows
        self.setStyleSheet("QLineEdit { padding-right: 20px; }")

        # Arrow buttons container (stacked vertically, child of this widget)
        arrow_container = QWidget(self)
        arrow_container.setFixedSize(18, 20)
        arrow_layout = QVBoxLayout(arrow_container)
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.setSpacing(-2)  # Negative spacing to bring them closer

        # Up button
        self.btnUp = QToolButton(arrow_container)
        self.btnUp.setText("▲")
        self.btnUp.setFixedSize(18, 10)
        self.btnUp.setAutoRepeat(True)
        self.btnUp.setAutoRepeatDelay(300)  # 300ms before auto-repeat starts
        self.btnUp.setAutoRepeatInterval(50)  # 50ms between repeats
        self.btnUp.clicked.connect(self.increment)
        arrow_layout.addWidget(self.btnUp)

        # Down button
        self.btnDown = QToolButton(arrow_container)
        self.btnDown.setText("▼")
        self.btnDown.setFixedSize(18, 10)
        self.btnDown.setAutoRepeat(True)
        self.btnDown.setAutoRepeatDelay(300)  # 300ms before auto-repeat starts
        self.btnDown.setAutoRepeatInterval(50)  # 50ms between repeats
        self.btnDown.clicked.connect(self.decrement)
        arrow_layout.addWidget(self.btnDown)

        # Store arrow container for positioning
        self.arrow_container = arrow_container

        # Connect signals
        self.editingFinished.connect(self.auto_format)

        # Style for buttons
        button_style = """
            QToolButton {
                border: none;
                background: transparent;
                color: #b0b0b0;
                font-size: 9px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:hover {
                color: #808080;
            }
            QToolButton:pressed {
                color: #606060;
            }
        """
        self.btnUp.setStyleSheet(button_style)
        self.btnDown.setStyleSheet(button_style)

    def resizeEvent(self, event):
        """Position the arrow container on the right side when resized"""
        super().resizeEvent(event)
        # Position arrow container on the right edge, vertically centered
        button_width = self.arrow_container.width()
        button_height = self.arrow_container.height()
        x = self.width() - button_width - 2
        y = (self.height() - button_height) // 2
        self.arrow_container.move(x, y)


    def auto_format(self):
        """Auto-add unit if missing"""
        text = self.text().strip()
        if not text:
            return

        # If it already has the unit, do nothing
        if self.unit in text:
            return

        # If it's just a number or has a prefix (k, M, m, etc.), add unit
        if re.match(r'^[\d.]+[kmMuUnNpPgG]?$', text, re.IGNORECASE):
            self.setText(text + self.unit)

    def parse_value(self):
        """Parse the current value to a base number"""
        text = self.text().strip().upper()
        if not text:
            return 0.0

        # Remove the unit
        text = text.replace(self.unit.upper(), '').replace(self.unit.lower(), '')
        text = text.strip()

        # Handle metric prefixes
        multipliers = {
            'P': 1e-12,  # pico
            'N': 1e-9,   # nano
            'U': 1e-6,   # micro
            'M': 1e-3,   # milli (for current)
            'K': 1e3,    # kilo
            'MEG': 1e6,  # mega
            'G': 1e9,    # giga
        }

        # Special case for M (could be milli or mega)
        # For resistors, M usually means mega
        # For current, m usually means milli
        if self.unit == 'A' and 'M' in text and not 'MEG' in text:
            # Current: M means milli
            multipliers['M'] = 1e-3
        elif self.unit == 'Ω':
            # Resistance: M means mega
            multipliers['M'] = 1e6

        # Extract number and prefix
        match = re.match(r'([\d.]+)\s*([A-Z]*)', text)
        if not match:
            try:
                return float(text)
            except:
                return 0.0

        number_str, prefix = match.groups()
        try:
            number = float(number_str)
        except:
            return 0.0

        # Apply multiplier
        if prefix and prefix in multipliers:
            return number * multipliers[prefix]

        return number

    def format_value(self, value):
        """Format a base value with appropriate prefix"""
        if value == 0:
            return f"0{self.unit}"

        abs_value = abs(value)

        # Helper function to format with trailing zeros removed
        def clean_format(val, decimals=6):
            formatted = f"{val:.{decimals}f}"
            # Remove trailing zeros and decimal point if not needed
            formatted = formatted.rstrip('0').rstrip('.')
            return formatted

        # Choose appropriate prefix
        if abs_value >= 1e9:
            return f"{clean_format(value/1e9)}G{self.unit}"
        elif abs_value >= 1e6:
            return f"{clean_format(value/1e6)}M{self.unit}"
        elif abs_value >= 1e3:
            return f"{clean_format(value/1e3)}k{self.unit}"
        elif abs_value >= 1:
            return f"{clean_format(value)}{self.unit}"
        elif abs_value >= 1e-3:
            return f"{clean_format(value*1e3)}m{self.unit}"
        elif abs_value >= 1e-6:
            return f"{clean_format(value*1e6)}u{self.unit}"
        elif abs_value >= 1e-9:
            return f"{clean_format(value*1e9)}n{self.unit}"
        else:
            return f"{clean_format(value*1e12)}p{self.unit}"

    def increment(self):
        """Increment the value"""
        current_value = self.parse_value()

        # Check if shift is pressed
        modifiers = QApplication.keyboardModifiers()
        shift_pressed = modifiers & Qt.KeyboardModifier.ShiftModifier

        # Determine increment amount
        if shift_pressed:
            increment = 10
        else:
            increment = 1

        # Calculate new value
        new_value = current_value + increment

        # Update text
        self.setText(self.format_value(new_value))

    def decrement(self):
        """Decrement the value"""
        current_value = self.parse_value()

        # Check if shift is pressed
        modifiers = QApplication.keyboardModifiers()
        shift_pressed = modifiers & Qt.KeyboardModifier.ShiftModifier

        # Determine decrement amount
        if shift_pressed:
            decrement = 10
        else:
            decrement = 1

        # Calculate new value (don't go below 0)
        new_value = max(0, current_value - decrement)

        # Update text
        self.setText(self.format_value(new_value))
