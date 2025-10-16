"""
Draggable button component for ECis-full application.
Handles component buttons that can be dragged to create components.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QMouseEvent


class DraggableButton(QPushButton):
    """A draggable button for components - drag only, no click placement"""
    def __init__(self, text, component_type, size_w, size_h):
        super().__init__(text)
        self.component_type = component_type
        self.size_w = size_w  # Width in grid cells
        self.size_h = size_h  # Height in grid cells
        self.setAcceptDrops(False)
        # Make the button visually bigger (twice as high)
        self.setMinimumHeight(64)  # Adjust as needed for your UI (default QPushButton is ~32px)

        # Track drag start position
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Store the position where the drag might start
            self.drag_start_position = event.pos()
        # Don't call super() to prevent clicked signal
        event.accept()

    def mouseMoveEvent(self, event):
        # Only start drag if mouse has moved and left button is pressed
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if self.drag_start_position is None:
            return

        # Check if we've moved enough to start a drag (minimum distance: 5 pixels)
        if (event.pos() - self.drag_start_position).manhattanLength() < 5:
            return

        # Start the drag operation
        self.start_drag()
        self.drag_start_position = None

    def mouseReleaseEvent(self, event):
        # Clear drag start position on release
        self.drag_start_position = None
        # Don't call super() to prevent clicked signal
        event.accept()

    def start_drag(self):
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.component_type}:{self.size_w}:{self.size_h}")

        # Create drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.lightGray)
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()

        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.exec(Qt.DropAction.CopyAction)
