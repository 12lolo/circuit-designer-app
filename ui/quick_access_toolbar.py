"""Quick Access Toolbar with customizable pinned actions"""

from PyQt6.QtWidgets import QToolBar, QWidgetAction, QWidget, QHBoxLayout, QLabel, QToolButton, QStyle, QMenu
from PyQt6.QtCore import QSettings, pyqtSignal, Qt
from PyQt6.QtGui import QAction, QIcon


class QuickAccessToolbar(QToolBar):
    """Customizable quick access toolbar"""

    # Default pinned actions
    DEFAULT_PINNED = ["New", "Open", "Save", "Run", "Undo", "Redo"]

    def __init__(self, parent=None):
        super().__init__("Quick Access", parent)
        self.setObjectName("QuickAccessToolbar")
        self.settings = QSettings("ECis", "CircuitDesigner")

        # Dictionary to store all available actions
        self.available_actions = {}

        # Load pinned action names
        self.pinned_actions = self.load_pinned_actions()

    def load_pinned_actions(self):
        """Load pinned actions from settings"""
        pinned = self.settings.value("quick_access/pinned", self.DEFAULT_PINNED)
        if not isinstance(pinned, list):
            pinned = self.DEFAULT_PINNED
        return pinned

    def save_pinned_actions(self):
        """Save pinned actions to settings"""
        self.settings.setValue("quick_access/pinned", self.pinned_actions)

    def register_action(self, action, name):
        """Register an action that can be pinned"""
        self.available_actions[name] = action

        # If this action is pinned, add it to toolbar
        if name in self.pinned_actions:
            self.add_action_to_toolbar(action, name)

    def add_action_to_toolbar(self, action, name):
        """Add an action to the toolbar"""
        # Don't add if already present
        for toolbar_action in self.actions():
            if toolbar_action.data() == name:
                return

        # Clone the action for the toolbar
        toolbar_action = QAction(action.icon(), action.text(), self)
        toolbar_action.setToolTip(action.toolTip())
        toolbar_action.setShortcut(action.shortcut())
        toolbar_action.setData(name)  # Store name for identification

        # Connect to same slot
        toolbar_action.triggered.connect(action.trigger)

        self.addAction(toolbar_action)

    def remove_action_from_toolbar(self, name):
        """Remove an action from the toolbar"""
        for action in self.actions():
            if action.data() == name:
                self.removeAction(action)
                break

    def pin_action(self, name):
        """Pin an action to the toolbar"""
        if name not in self.pinned_actions and name in self.available_actions:
            self.pinned_actions.append(name)
            self.save_pinned_actions()
            self.add_action_to_toolbar(self.available_actions[name], name)

    def unpin_action(self, name):
        """Unpin an action from the toolbar"""
        if name in self.pinned_actions:
            self.pinned_actions.remove(name)
            self.save_pinned_actions()
            self.remove_action_from_toolbar(name)

    def is_pinned(self, name):
        """Check if an action is pinned"""
        return name in self.pinned_actions

    def toggle_pin(self, name):
        """Toggle pin state of an action"""
        if self.is_pinned(name):
            self.unpin_action(name)
        else:
            self.pin_action(name)

    def rebuild_toolbar(self):
        """Rebuild the entire toolbar from pinned actions"""
        # Clear toolbar
        self.clear()

        # Re-add all pinned actions in order
        for name in self.pinned_actions:
            if name in self.available_actions:
                self.add_action_to_toolbar(self.available_actions[name], name)


class PinnableMenuAction(QWidgetAction):
    """A menu action with a pin button"""

    def __init__(self, action, name, toolbar, parent=None):
        super().__init__(parent)
        self.action = action
        self.name = name
        self.toolbar = toolbar

    def createWidget(self, parent):
        """Create the widget for this action"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(5)

        # Pin button
        self.pin_button = QToolButton(widget)
        self.pin_button.setFixedSize(20, 20)
        self.pin_button.setAutoRaise(True)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.update_pin_button()
        layout.addWidget(self.pin_button)

        # Action label (clickable)
        action_widget = QWidget(widget)
        action_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 5, 5, 5)

        # Action text
        text_label = QLabel(self.name, action_widget)
        action_layout.addWidget(text_label)
        action_layout.addStretch()

        # Shortcut text
        shortcut = self.action.shortcut()
        if not shortcut.isEmpty():
            shortcut_label = QLabel(shortcut.toString(), action_widget)
            shortcut_label.setStyleSheet("color: gray; font-size: 10px;")
            action_layout.addWidget(shortcut_label)

        # Make the action widget clickable
        action_widget.mousePressEvent = lambda e: self.trigger_action()

        layout.addWidget(action_widget, 1)

        widget.setStyleSheet("""
            QWidget:hover {
                background-color: palette(highlight);
            }
        """)

        return widget

    def update_pin_button(self):
        """Update pin button appearance"""
        if self.toolbar.is_pinned(self.name):
            self.pin_button.setText("📌")
            self.pin_button.setToolTip("Unpin from toolbar")
        else:
            self.pin_button.setText("📍")
            self.pin_button.setToolTip("Pin to toolbar")

    def toggle_pin(self):
        """Toggle pin state"""
        self.toolbar.toggle_pin(self.name)
        self.update_pin_button()

    def trigger_action(self):
        """Trigger the original action"""
        # Find and close the parent menu
        parent = self.parent()
        if parent:
            # Walk up the widget tree to find the QMenu
            widget = parent
            while widget:
                if isinstance(widget, QMenu):
                    widget.close()
                    break
                widget = widget.parentWidget()

        # Trigger the action
        self.action.trigger()


def make_menu_pinnable(menu, toolbar, action, name):
    """Make a menu action pinnable by adding a pin button"""
    # Create pinnable action
    pinnable_action = PinnableMenuAction(action, name, toolbar, menu)

    # Add to menu
    menu.addAction(pinnable_action)
