"""
Component item for ECis-full application.
Handles graphical components that can be placed and manipulated in the circuit.
"""

import math
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPixmap, QPainter
from .connection_points import ConnectionPoint


class ComponentItem(QGraphicsRectItem):
    """A draggable component item in the graphics scene"""
    def __init__(self, component_type, size_w, size_h, grid_spacing):
        self.grid_spacing = grid_spacing
        self.component_type = component_type
        self.size_w = size_w
        self.size_h = size_h
        self.name = component_type  # Default name
        self.value = self.get_default_value()  # Component value
        self.orientation = 0  # Default orientation in degrees
        self.net_id = ""  # Network ID for circuit analysis

        # Create rectangle based on grid size
        width = size_w * grid_spacing
        height = size_h * grid_spacing
        super().__init__(0, 0, width, height)

        # Set appearance
        self.setBrush(QBrush(QColor(240, 240, 255)))  # Slightly lighter background
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # Set z-value to render components above wires
        self.setZValue(50)

        # Create and add icon instead of text label
        self.icon_item = self.create_component_icon()
        if self.icon_item:
            self.icon_item.setParentItem(self)

        # Make it movable and selectable
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsFocusable)

        # Create connection points based on component type
        self.connection_points = []
        self.create_connection_points()

    def get_default_value(self):
        """Get default value based on component type"""
        if self.component_type == "Weerstand":
            return "1kΩ"
        elif self.component_type == "Vdc":
            return "5V"
        elif self.component_type == "Spannings Bron":
            return "12V"
        elif self.component_type == "Isrc":
            return "1mA"
        elif self.component_type == "GND":
            return "0V"
        return ""

    def keyPressEvent(self, event):
        """Handle key press events for rotation"""
        # Let the main window handle rotation to avoid conflicts
        # Pass all key events to the parent (scene/main window)
        super().keyPressEvent(event)

    def rotate_component(self, degrees):
        """Rotate the component by the specified degrees"""
        # Store existing wire connections before rotation
        old_connections = []
        for point in self.connection_points:
            for wire in point.connected_wires[:]:  # Copy list to avoid modification during iteration
                # Store wire and which end connects to this point
                if hasattr(wire, 'start_point') and wire.start_point == point:
                    old_connections.append((wire, 'start', point.point_id))
                elif hasattr(wire, 'end_point') and wire.end_point == point:
                    old_connections.append((wire, 'end', point.point_id))

        self.orientation = (self.orientation + degrees) % 360

        # Update the graphics transformation
        self.setRotation(self.orientation)

        # Recreate connection points with new positions
        self.remove_connection_points()
        self.create_connection_points()

        # Reconnect wires to the new connection points
        for wire, connection_type, old_point_id in old_connections:
            # Find the corresponding new connection point
            new_point = None
            for point in self.connection_points:
                if point.point_id == old_point_id:
                    new_point = point
                    break

            if new_point:
                # Reconnect the wire to the new connection point
                if connection_type == 'start':
                    wire.start_point = new_point
                elif connection_type == 'end':
                    wire.end_point = new_point

                # Add wire to new connection point's list
                new_point.connected_wires.append(wire)

                # Update the wire's visual position
                wire.update_position()

        # Update inspect panel if this component is selected
        scene = self.scene()
        if scene and self.isSelected():
            main_window = scene.views()[0].main_window
            if hasattr(main_window, 'on_component_selected'):
                main_window.on_component_selected(self)

        # Log the rotation
        if scene:
            main_window = scene.views()[0].main_window
            if hasattr(main_window, 'log_panel'):
                main_window.log_panel.log_message(f"[INFO] {self.name} geroteerd naar {self.orientation}°")

    def remove_connection_points(self):
        """Remove existing connection points"""
        for point in self.connection_points:
            # Clear wire connections from this point
            point.connected_wires.clear()
            if point.scene():
                point.scene().removeItem(point)
        self.connection_points.clear()

    def mousePressEvent(self, event):
        # Handle selection
        if event.button() == Qt.MouseButton.LeftButton:
            # Clear other selections first
            scene = self.scene()
            if scene:
                for item in scene.selectedItems():
                    item.setSelected(False)

                # Select this item
                self.setSelected(True)
                self.setFocus()  # Set focus to enable keyboard events

                # Update inspect panel using the new method
                main_window = scene.views()[0].main_window
                if hasattr(main_window, 'on_component_selected'):
                    main_window.on_component_selected(self)

        super().mousePressEvent(event)

    def itemChange(self, change, value):
        """Handle item changes like selection"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Item is being selected
                # Update appearance when selected
                self.setPen(QPen(QColor(255, 0, 0), 3))  # Red border when selected
                self.setZValue(500)  # Bring to front when selected
            else:  # Item is being deselected
                # Return to normal appearance
                self.setPen(QPen(QColor(0, 0, 0), 2))  # Black border normally
                self.setZValue(50)  # Return to normal z-value

        return super().itemChange(change, value)

    def update_from_inspect_panel(self, name, value, orientation, net_id):
        """Update component properties from inspect panel"""
        old_orientation = self.orientation

        self.name = name
        self.value = value
        new_orientation = int(orientation.replace("°", ""))
        self.net_id = net_id

        # Handle orientation change
        if new_orientation != old_orientation:
            rotation_diff = new_orientation - old_orientation
            self.rotate_component(rotation_diff)

        # Update the icon based on the new component type
        new_icon_item = self.create_component_icon()
        if new_icon_item:
            # Remove old icon
            if self.icon_item and self.icon_item.scene():
                self.icon_item.scene().removeItem(self.icon_item)

            # Set new icon
            new_icon_item.setParentItem(self)
            self.icon_item = new_icon_item

    def create_connection_points(self):
        """Create connection points based on component type and orientation"""
        # Get the actual rectangle dimensions
        rect = self.rect()
        width = rect.width()
        height = rect.height()

        if self.component_type == "Weerstand":  # Resistor: connections on the ends
            if self.orientation == 0:  # Horizontal
                left_point = ConnectionPoint(self, 0, height/2, "in")
                right_point = ConnectionPoint(self, width, height/2, "out")
            elif self.orientation == 90:  # Vertical
                left_point = ConnectionPoint(self, width/2, 0, "in")
                right_point = ConnectionPoint(self, width/2, height, "out")
            elif self.orientation == 180:  # Horizontal flipped
                left_point = ConnectionPoint(self, width, height/2, "in")
                right_point = ConnectionPoint(self, 0, height/2, "out")
            else:  # 270 - Vertical flipped
                left_point = ConnectionPoint(self, width/2, height, "in")
                right_point = ConnectionPoint(self, width/2, 0, "out")

            self.connection_points.append(left_point)
            self.connection_points.append(right_point)

        elif self.component_type in ["Spannings Bron", "Isrc"]:  # Sources: connections on top/bottom or left/right
            if self.orientation == 0:  # Normal - top and bottom
                top_point = ConnectionPoint(self, width/2, 0, "pos")
                bottom_point = ConnectionPoint(self, width/2, height, "neg")
            elif self.orientation == 90:  # 90 degrees - right and left
                top_point = ConnectionPoint(self, width, height/2, "pos")
                bottom_point = ConnectionPoint(self, 0, height/2, "neg")
            elif self.orientation == 180:  # 180 degrees - bottom and top
                top_point = ConnectionPoint(self, width/2, height, "pos")
                bottom_point = ConnectionPoint(self, width/2, 0, "neg")
            else:  # 270 degrees - left and right
                top_point = ConnectionPoint(self, 0, height/2, "pos")
                bottom_point = ConnectionPoint(self, width, height/2, "neg")

            self.connection_points.append(top_point)
            self.connection_points.append(bottom_point)

        elif self.component_type in ["Vdc", "GND"]:  # Single connection components
            # Center connection point
            center_point = ConnectionPoint(self, width/2, height/2, "terminal")
            self.connection_points.append(center_point)

    def mouseReleaseEvent(self, event):
        # Snap to grid when released
        self.snap_to_grid()
        # Update all connected wires
        self.update_connected_wires()
        super().mouseReleaseEvent(event)

    def snap_to_grid(self):
        """Snap the component to the nearest grid position"""
        pos = self.pos()
        # Calculate nearest grid position
        grid_x = round(pos.x() / self.grid_spacing) * self.grid_spacing
        grid_y = round(pos.y() / self.grid_spacing) * self.grid_spacing
        self.setPos(grid_x, grid_y)

    def update_connected_wires(self):
        """Update positions of all wires connected to this component"""
        for point in self.connection_points:
            for wire in point.connected_wires:
                wire.update_position()

    def create_component_icon(self):
        """Create a visual icon for the component based on its type"""
        rect = self.rect()
        width = rect.width()
        height = rect.height()

        if self.component_type == "Weerstand":
            return self.create_resistor_icon(width, height)
        elif self.component_type == "Vdc":
            return self.create_vdc_icon(width, height)
        elif self.component_type == "GND":
            return self.create_ground_icon(width, height)
        elif self.component_type == "Spannings Bron":
            return self.create_voltage_source_icon(width, height)
        elif self.component_type == "Isrc":
            return self.create_current_source_icon(width, height)
        return None

    def create_resistor_icon(self, width, height):
        """Create a resistor icon (zigzag pattern)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        # Draw zigzag resistor pattern
        center_y = height / 2
        segment_width = width / 8
        zigzag_height = height / 4

        # Draw the zigzag
        points = []
        for i in range(9):
            x = i * segment_width
            if i == 0 or i == 8:
                y = center_y
            elif i % 2 == 1:
                y = center_y - zigzag_height
            else:
                y = center_y + zigzag_height
            points.append(QPointF(x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def create_vdc_icon(self, width, height):
        """Create a DC voltage source icon (+ and - symbols)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_x = width / 2
        center_y = height / 2

        # Draw circle
        radius = min(width, height) / 3
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # Draw + and - symbols
        plus_size = radius / 3
        painter.drawLine(QPointF(center_x - plus_size, center_y - plus_size),
                        QPointF(center_x + plus_size, center_y - plus_size))
        painter.drawLine(QPointF(center_x, center_y - plus_size - plus_size),
                        QPointF(center_x, center_y - plus_size + plus_size))

        painter.drawLine(QPointF(center_x - plus_size, center_y + plus_size),
                        QPointF(center_x + plus_size, center_y + plus_size))

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def create_ground_icon(self, width, height):
        """Create a ground symbol icon"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_x = width / 2
        bottom_y = height * 0.8

        # Draw ground symbol (three horizontal lines of decreasing length)
        line_spacing = height / 8
        for i in range(3):
            line_width = (width / 2) - (i * width / 8)
            y = bottom_y - (i * line_spacing)
            painter.drawLine(QPointF(center_x - line_width, y),
                           QPointF(center_x + line_width, y))

        # Draw vertical line to center
        painter.drawLine(QPointF(center_x, height / 4),
                        QPointF(center_x, bottom_y))

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def create_voltage_source_icon(self, width, height):
        """Create a voltage source icon (circle with sine wave)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_x = width / 2
        center_y = height / 2

        # Draw circle
        radius = min(width, height) / 3
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # Draw sine wave inside
        wave_points = []
        wave_width = radius * 1.4
        wave_height = radius / 2
        for x in range(int(-wave_width/2), int(wave_width/2), 2):
            y = wave_height * math.sin(x * 2 * math.pi / wave_width * 2)
            wave_points.append(QPointF(center_x + x, center_y + y))

        for i in range(len(wave_points) - 1):
            painter.drawLine(wave_points[i], wave_points[i + 1])

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def create_current_source_icon(self, width, height):
        """Create a current source icon (circle with arrow)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_x = width / 2
        center_y = height / 2

        # Draw circle
        radius = min(width, height) / 3
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # Draw arrow pointing up
        arrow_height = radius * 1.2
        arrow_width = radius / 3

        # Arrow shaft
        painter.drawLine(QPointF(center_x, center_y + arrow_height/2),
                        QPointF(center_x, center_y - arrow_height/2))

        # Arrow head
        painter.drawLine(QPointF(center_x, center_y - arrow_height/2),
                        QPointF(center_x - arrow_width, center_y - arrow_height/2 + arrow_width))
        painter.drawLine(QPointF(center_x, center_y - arrow_height/2),
                        QPointF(center_x + arrow_width, center_y - arrow_height/2 + arrow_width))

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item
