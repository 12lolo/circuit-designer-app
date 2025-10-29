"""Keyboard shortcuts settings dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QKeySequence


class ShortcutEditor(QLineEdit):
    """Custom line edit for capturing keyboard shortcuts"""

    shortcut_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click and press keys...")
        self.current_shortcut = ""

    def keyPressEvent(self, event):
        """Capture key press and convert to shortcut string"""
        # Ignore just modifier keys
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        # Get the key sequence - convert modifiers to int value
        modifiers_value = int(event.modifiers().value)
        key_sequence = QKeySequence(event.key() | modifiers_value)
        shortcut_str = key_sequence.toString()

        self.setText(shortcut_str)
        self.current_shortcut = shortcut_str
        self.shortcut_changed.emit(shortcut_str)

    def get_shortcut(self):
        """Get the current shortcut string"""
        return self.current_shortcut

    def set_shortcut(self, shortcut_str):
        """Set the shortcut display"""
        self.current_shortcut = shortcut_str
        self.setText(shortcut_str)


class ShortcutsDialog(QDialog):
    """Dialog for viewing and editing keyboard shortcuts"""

    # Default shortcuts mapping (action_name -> shortcut_string)
    DEFAULT_SHORTCUTS = {
        # File operations
        "New": "Ctrl+N",
        "Open": "Ctrl+O",
        "Save": "Ctrl+S",
        "Save Copy": "Ctrl+Shift+S",
        "Export PNG": "Ctrl+E",

        # Edit operations
        "Undo": "Ctrl+Z",
        "Redo": "Ctrl+Shift+Z",
        "Copy": "Ctrl+C",
        "Paste": "Ctrl+V",
        "Select All": "Ctrl+A",
        "Deselect All": "Ctrl+D",

        # View operations
        "Zoom In": "Ctrl+=",
        "Zoom Out": "Ctrl+-",
        "Reset Zoom": "Ctrl+0",
        "Center View": "Home",
        "Focus Canvas": "F1",
        "Clear Log": "Ctrl+L",

        # Simulation
        "Run Simulation": "F5",
        "Copy Output": "Ctrl+Shift+C",
    }

    # Categories for organizing shortcuts
    CATEGORIES = {
        "File": ["New", "Open", "Save", "Save Copy", "Export PNG"],
        "Edit": ["Undo", "Redo", "Copy", "Paste", "Select All", "Deselect All"],
        "View": ["Zoom In", "Zoom Out", "Reset Zoom", "Center View", "Focus Canvas", "Clear Log"],
        "Simulation": ["Run Simulation", "Copy Output"],
    }

    def __init__(self, toolbar_manager, parent=None):
        super().__init__(parent)
        self.toolbar_manager = toolbar_manager
        self.settings = QSettings("ECis", "CircuitDesigner")
        self.modified_shortcuts = {}  # Track changes
        self.setupUi()
        self.load_shortcuts()

    def setupUi(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Info label
        info = QLabel("Click on a shortcut cell to change it, then press your desired key combination.")
        info.setStyleSheet("color: #666; padding: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Table for shortcuts
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["Category", "Action", "Shortcut"])

        # Set column widths
        header = self.shortcuts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.shortcuts_table.setAlternatingRowColors(True)
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.shortcuts_table, 1)

        # Button layout
        button_layout = QHBoxLayout()

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_shortcuts)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def load_shortcuts(self):
        """Load shortcuts and populate the table"""
        row = 0

        for category, actions in self.CATEGORIES.items():
            for action in actions:
                # Get shortcut (from settings or default)
                shortcut_key = f"shortcuts/{action}"
                default_shortcut = self.DEFAULT_SHORTCUTS.get(action, "")
                current_shortcut = self.settings.value(shortcut_key, default_shortcut)

                # Add row
                self.shortcuts_table.insertRow(row)

                # Category
                category_item = QTableWidgetItem(category)
                category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.shortcuts_table.setItem(row, 0, category_item)

                # Action
                action_item = QTableWidgetItem(action)
                action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.shortcuts_table.setItem(row, 1, action_item)

                # Shortcut (editable)
                shortcut_editor = ShortcutEditor()
                shortcut_editor.set_shortcut(current_shortcut)
                shortcut_editor.shortcut_changed.connect(
                    lambda s, a=action: self.on_shortcut_changed(a, s)
                )
                self.shortcuts_table.setCellWidget(row, 2, shortcut_editor)

                row += 1

    def on_shortcut_changed(self, action, shortcut):
        """Handle shortcut change"""
        # Check for conflicts
        conflicts = []
        for r in range(self.shortcuts_table.rowCount()):
            other_action = self.shortcuts_table.item(r, 1).text()
            if other_action != action:
                other_editor = self.shortcuts_table.cellWidget(r, 2)
                if isinstance(other_editor, ShortcutEditor):
                    if other_editor.get_shortcut() == shortcut and shortcut:
                        conflicts.append(other_action)

        if conflicts:
            QMessageBox.warning(
                self,
                "Shortcut Conflict",
                f"The shortcut '{shortcut}' is already used by:\n" + "\n".join(conflicts) +
                "\n\nPlease choose a different shortcut or clear the conflicting one first."
            )
            # Don't save this change
            return

        # Track the modification
        self.modified_shortcuts[action] = shortcut

    def reset_to_defaults(self):
        """Reset all shortcuts to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Are you sure you want to reset all shortcuts to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear all custom shortcuts from settings
            self.settings.remove("shortcuts")

            # Reload the table
            self.shortcuts_table.setRowCount(0)
            self.load_shortcuts()

            # Clear modifications
            self.modified_shortcuts.clear()

            QMessageBox.information(self, "Reset Complete", "All shortcuts have been reset to defaults.")

    def apply_shortcuts(self):
        """Apply the modified shortcuts"""
        # Save all shortcuts to settings
        for row in range(self.shortcuts_table.rowCount()):
            action = self.shortcuts_table.item(row, 1).text()
            editor = self.shortcuts_table.cellWidget(row, 2)

            if isinstance(editor, ShortcutEditor):
                shortcut = editor.get_shortcut()
                shortcut_key = f"shortcuts/{action}"
                self.settings.setValue(shortcut_key, shortcut)

        # Update the actual shortcuts in the toolbar manager
        self.update_toolbar_shortcuts()

        QMessageBox.information(
            self,
            "Shortcuts Applied",
            "Shortcuts have been updated successfully.\nSome shortcuts may require restarting the application to take full effect."
        )

        self.accept()

    def update_toolbar_shortcuts(self):
        """Update shortcuts in the toolbar manager"""
        # Map action names to toolbar manager actions
        action_map = {
            "New": self.toolbar_manager.actionNieuw,
            "Open": self.toolbar_manager.actionOpenen,
            "Save": self.toolbar_manager.actionOpslaan,
            "Save Copy": self.toolbar_manager.actionSaveCopy,
            "Run Simulation": self.toolbar_manager.actionRun,
            "Undo": self.toolbar_manager.actionUndo,
            "Redo": self.toolbar_manager.actionRedo,
            "Copy": self.toolbar_manager.actionCopy,
            "Paste": self.toolbar_manager.actionPaste,
            "Copy Output": self.toolbar_manager.actionCopyOutput,
            "Select All": self.toolbar_manager.actionSelectAll,
            "Deselect All": self.toolbar_manager.actionDeselectAll,
            "Focus Canvas": self.toolbar_manager.actionFocusCanvas,
            "Clear Log": self.toolbar_manager.actionClearLog,
            "Zoom In": self.toolbar_manager.actionZoomIn,
            "Zoom Out": self.toolbar_manager.actionZoomOut,
            "Reset Zoom": self.toolbar_manager.actionZoomReset,
            "Center View": self.toolbar_manager.actionCenterView,
            "Export PNG": self.toolbar_manager.actionExportPNG,
        }

        for action_name, action in action_map.items():
            shortcut_key = f"shortcuts/{action_name}"
            default_shortcut = self.DEFAULT_SHORTCUTS.get(action_name, "")
            shortcut = self.settings.value(shortcut_key, default_shortcut)

            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            else:
                action.setShortcut(QKeySequence())
