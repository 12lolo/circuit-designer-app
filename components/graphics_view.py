"""
Graphics view for ECis-full application.
Handles the droppable graphics view for circuit components.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from .component_item import ComponentItem


class DroppableGraphicsView(QGraphicsView):
    """Custom graphics view that accepts drops"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.grid_spacing = 40  # Will be updated when grid is drawn

        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set up zoom parameters
        self.zoom_factor = 1.15
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        self.current_zoom = 1.0

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            data = event.mimeData().text().split(':')
            if len(data) == 3:
                component_type, size_w, size_h = data
                size_w, size_h = int(size_w), int(size_h)

                # Convert drop position to scene coordinates
                scene_pos = self.mapToScene(event.position().toPoint())

                # Create component item
                component = ComponentItem(component_type, size_w, size_h, self.grid_spacing)
                component.setPos(scene_pos)
                component.snap_to_grid()

                # Add to scene
                self.scene().addItem(component)

                # Log the action using the new log panel
                if hasattr(self.main_window, 'log_panel'):
                    self.main_window.log_panel.log_message(f"[INFO] {component_type} geplaatst op grid")

                event.acceptProposedAction()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming and scrolling"""
        # Check if Ctrl is pressed for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl + scroll
            zoom_in = event.angleDelta().y() > 0
            zoom_factor = self.zoom_factor if zoom_in else 1.0 / self.zoom_factor

            # Calculate new zoom level
            new_zoom = self.current_zoom * zoom_factor

            # Clamp zoom within limits
            if new_zoom < self.zoom_min:
                zoom_factor = self.zoom_min / self.current_zoom
                new_zoom = self.zoom_min
            elif new_zoom > self.zoom_max:
                zoom_factor = self.zoom_max / self.current_zoom
                new_zoom = self.zoom_max

            if zoom_factor != 1.0:
                # Get mouse position for zoom center
                mouse_pos = event.position()
                scene_pos = self.mapToScene(mouse_pos.toPoint())

                # Apply zoom
                self.scale(zoom_factor, zoom_factor)
                self.current_zoom = new_zoom

                # Center zoom on mouse position
                new_mouse_pos = self.mapFromScene(scene_pos)
                delta = new_mouse_pos - mouse_pos.toPoint()
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())

                # Log zoom action using the new log panel
                if hasattr(self.main_window, 'log_panel'):
                    self.main_window.log_panel.log_message(f"[INFO] Zoom: {self.current_zoom:.1f}x")

            event.accept()
        else:
            # Normal scrolling
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+Plus/Minus for zoom
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.zoom_in()
                event.accept()
                return
            elif key == Qt.Key.Key_Minus:
                self.zoom_out()
                event.accept()
                return
            elif key == Qt.Key.Key_0:
                self.reset_zoom()
                event.accept()
                return

        # Arrow keys for panning
        pan_distance = 50
        if key == Qt.Key.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - pan_distance)
            event.accept()
            return
        elif key == Qt.Key.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + pan_distance)
            event.accept()
            return
        elif key == Qt.Key.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - pan_distance)
            event.accept()
            return
        elif key == Qt.Key.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + pan_distance)
            event.accept()
            return

        # Home key to center view
        elif key == Qt.Key.Key_Home:
            self.center_view()
            event.accept()
            return

        # Pass other events to parent
        super().keyPressEvent(event)

    def zoom_in(self):
        """Zoom in centered on viewport"""
        if self.current_zoom < self.zoom_max:
            zoom_factor = min(self.zoom_factor, self.zoom_max / self.current_zoom)
            self.scale(zoom_factor, zoom_factor)
            self.current_zoom *= zoom_factor
            if hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.log_message(f"[INFO] Zoom in: {self.current_zoom:.1f}x")

    def zoom_out(self):
        """Zoom out centered on viewport"""
        if self.current_zoom > self.zoom_min:
            zoom_factor = max(1.0 / self.zoom_factor, self.zoom_min / self.current_zoom)
            self.scale(zoom_factor, zoom_factor)
            self.current_zoom *= zoom_factor
            if hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.log_message(f"[INFO] Zoom out: {self.current_zoom:.1f}x")

    def reset_zoom(self):
        """Reset zoom to 100%"""
        zoom_factor = 1.0 / self.current_zoom
        self.scale(zoom_factor, zoom_factor)
        self.current_zoom = 1.0
        if hasattr(self.main_window, 'log_panel'):
            self.main_window.log_panel.log_message("[INFO] Zoom reset: 1.0x")

    def center_view(self):
        """Center the view on the scene"""
        scene_rect = self.scene().itemsBoundingRect()
        if not scene_rect.isEmpty():
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.current_zoom = self.transform().m11()  # Get current scale
        else:
            # If no items, center on origin
            self.centerOn(0, 0)
        if hasattr(self.main_window, 'log_panel'):
            self.main_window.log_panel.log_message("[INFO] View centered")

    def mousePressEvent(self, event):
        """Handle mouse press events for panning"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning with middle mouse button
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Stop panning
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
