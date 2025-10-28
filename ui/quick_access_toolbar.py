"""Quick Access Toolbar with customizable pinned actions"""

from PyQt6.QtWidgets import QToolBar, QWidgetAction, QWidget, QHBoxLayout, QLabel, QToolButton, QStyle, QMenu, QApplication
from PyQt6.QtCore import QSettings, pyqtSignal, Qt, QMimeData, QByteArray, QPoint
from PyQt6.QtGui import QAction, QIcon, QDrag, QPainter, QPen, QColor


class QuickAccessToolbar(QToolBar):
    """Customizable quick access toolbar with draggable buttons"""

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

        # Enable drag and drop
        self.setAcceptDrops(True)
        self.drag_start_position = None
        self.drop_indicator_pos = None  # Position to draw drop indicator

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
        toolbar_action.setToolTip(action.toolTip() + "\n(Drag to reorder)")
        toolbar_action.setShortcut(action.shortcut())
        toolbar_action.setData(name)  # Store name for identification

        # Connect to same slot
        toolbar_action.triggered.connect(action.trigger)

        self.addAction(toolbar_action)

        # Get the button widget created for this action and make it draggable
        button = self.widgetForAction(toolbar_action)
        if button:
            button.setAcceptDrops(True)
            # Store action name in button for later retrieval
            button.setProperty("action_name", name)
            # Install event filter to intercept mouse events
            button.installEventFilter(self)

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

    def eventFilter(self, watched, event):
        """Filter events from toolbar buttons to handle dragging"""
        # Check if this is a button with an action name
        if hasattr(watched, 'property'):
            action_name = watched.property("action_name")
            if action_name:
                # Handle mouse press
                if event.type() == event.Type.MouseButtonPress:
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.drag_start_position = event.pos()
                        self.dragged_action_name = action_name
                        self.dragged_button = watched
                        return False  # Let the event continue

                # Handle mouse move
                elif event.type() == event.Type.MouseMove:
                    if (event.buttons() & Qt.MouseButton.LeftButton) and \
                       hasattr(self, 'drag_start_position') and self.drag_start_position is not None:

                        # Check if we've moved far enough to start a drag
                        if (event.pos() - self.drag_start_position).manhattanLength() >= 10:
                            # Start drag operation
                            drag = QDrag(watched)
                            mime_data = QMimeData()
                            mime_data.setText(action_name)
                            drag.setMimeData(mime_data)

                            # Create a pixmap of the button being dragged
                            pixmap = watched.grab()
                            drag.setPixmap(pixmap)
                            drag.setHotSpot(pixmap.rect().center())

                            # Clear drag start position
                            self.drag_start_position = None

                            # Execute drag
                            drag.exec(Qt.DropAction.MoveAction)
                            return True  # Event handled

        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        """Accept drag events with text data"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Accept drag move events and show drop indicator"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

            # Calculate drop indicator position
            drop_pos = event.position().toPoint()
            target_button = self.childAt(drop_pos)

            if not target_button or not hasattr(target_button, 'property'):
                target_button = self._find_closest_button(drop_pos)

            if target_button and hasattr(target_button, 'property'):
                target_name = target_button.property("action_name")
                if target_name:
                    # Get the center X of the target button
                    target_center_x = target_button.x() + target_button.width() / 2
                    drop_x = drop_pos.x()

                    # Determine if indicator should be on left or right
                    if drop_x <= target_center_x:
                        # Insert before - show line on left edge
                        self.drop_indicator_pos = target_button.x()
                    else:
                        # Insert after - show line on right edge
                        self.drop_indicator_pos = target_button.x() + target_button.width()

                    self.update()  # Trigger repaint
        else:
            self.drop_indicator_pos = None
            self.update()

    def dropEvent(self, event):
        """Handle drop event to reorder buttons horizontally"""
        # Clear drop indicator
        self.drop_indicator_pos = None
        self.update()

        if not event.mimeData().hasText():
            return

        dragged_name = event.mimeData().text()
        drop_pos = event.position().toPoint()

        # Find the button at the drop position
        target_button = self.childAt(drop_pos)
        if not target_button or not hasattr(target_button, 'property'):
            # If not dropped on a button, try to find the closest button
            target_button = self._find_closest_button(drop_pos)

        if target_button and hasattr(target_button, 'property'):
            target_name = target_button.property("action_name")

            if target_name and target_name != dragged_name:
                # Reorder the pinned_actions list
                try:
                    # Remove the dragged action from its current position
                    old_index = self.pinned_actions.index(dragged_name)
                    self.pinned_actions.pop(old_index)

                    # Find new position
                    new_index = self.pinned_actions.index(target_name)

                    # Determine if we should insert before or after target based on position
                    # Get the center X of the target button
                    target_center_x = target_button.x() + target_button.width() / 2
                    drop_x = drop_pos.x()

                    # If dropped on the right half of target, insert after
                    if drop_x > target_center_x:
                        new_index += 1

                    # Insert at new position
                    self.pinned_actions.insert(new_index, dragged_name)

                    # Save and rebuild
                    self.save_pinned_actions()
                    self.rebuild_toolbar()

                    event.acceptProposedAction()
                except (ValueError, IndexError):
                    pass

    def dragLeaveEvent(self, event):
        """Clear drop indicator when drag leaves toolbar"""
        self.drop_indicator_pos = None
        self.update()

    def paintEvent(self, event):
        """Draw drop indicator line"""
        super().paintEvent(event)

        # Draw drop indicator if dragging
        if self.drop_indicator_pos is not None:
            painter = QPainter(self)
            pen = QPen(QColor(0, 120, 215), 3)  # Blue line, 3px wide
            painter.setPen(pen)

            # Draw vertical line at drop position
            line_height = self.height()
            painter.drawLine(
                int(self.drop_indicator_pos), 0,
                int(self.drop_indicator_pos), line_height
            )
            painter.end()

    def _find_closest_button(self, pos):
        """Find the closest button to the given position"""
        closest_button = None
        min_distance = float('inf')

        for action in self.actions():
            button = self.widgetForAction(action)
            if button and hasattr(button, 'property'):
                action_name = button.property("action_name")
                if action_name:
                    # Calculate distance to button center
                    button_center = QPoint(
                        button.x() + button.width() // 2,
                        button.y() + button.height() // 2
                    )
                    distance = (pos - button_center).manhattanLength()

                    if distance < min_distance:
                        min_distance = distance
                        closest_button = button

        return closest_button


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
