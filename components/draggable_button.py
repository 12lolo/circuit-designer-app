"""
Draggable button component for ECis-full application.
Handles component buttons that can be dragged to create components.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QPixmap, QPainter


class DraggableButton(QPushButton):
    """A draggable button for components"""
    def __init__(self, text, component_type, size_w, size_h):
        super().__init__(text)
        self.component_type = component_type
        self.size_w = size_w  # Width in grid cells
        self.size_h = size_h  # Height in grid cells
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag()
        super().mousePressEvent(event)

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
