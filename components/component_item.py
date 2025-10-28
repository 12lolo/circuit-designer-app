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
        self.size_w = size_w  # in grid cells (original orientation width)
        self.size_h = size_h  # in grid cells (original orientation height)
        self.name = component_type  # Default name
        self.value = self.get_default_value()  # Component value
        self.orientation = 0  # Default orientation in degrees (0,90,180,270)
        self.net_id = ""  # Network ID for circuit analysis

        # Create rectangle based on grid size (base orientation 0)
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
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # Define component categories
        self.single_connection_types = {"Vdc", "GND", "Light"}

        # Initialize transform origin to anchor point
        self.update_transform_origin()

        # Create connection points based on component type
        self.connection_points = []
        self.create_connection_points()

    def get_default_value(self):
        """Get default value based on component type"""
        if self.component_type == "Resistor":
            return "1Ω"
        elif self.component_type == "Vdc":
            return "5V"
        elif self.component_type == "Switch":
            return "Open"
        elif self.component_type == "Light":
            return "Off"
        elif self.component_type == "GND":
            return "0V"
        return ""

    def keyPressEvent(self, event):
        """Handle key press events for rotation"""
        # Let the main window handle rotation to avoid conflicts
        # Pass all key events to the parent (scene/main window)
        super().keyPressEvent(event)

    def compute_effective_cell_dimensions(self):
        """Return effective (width_cells, height_cells) given current orientation.
        Orientation 0/180 => original size_w x size_h.
        Orientation 90/270 => swapped (size_h x size_w).
        """
        if self.orientation in (0, 180):
            return self.size_w, self.size_h
        else:
            return self.size_h, self.size_w

    def get_rotation_origin_local(self):
        """Rotation always about geometric center for visual stability."""
        rect = self.rect()
        return QPointF(rect.width()/2.0, rect.height()/2.0)

    def update_transform_origin(self):
        """Update transform origin (independent of snapping anchor)."""
        self.setTransformOriginPoint(self.get_rotation_origin_local())

    def get_anchor_local_pos(self):
        """Return local anchor for snapping & occupancy: fixed top-left (0,0) of the rect.
        Connection points have been adjusted separately so at least one terminal lies on a grid junction.
        Keeping a stable top-left anchor avoids orientation-dependent footprint shifts when checking overlaps.
        """
        return QPointF(0, 0)

    def rotate_component(self, degrees):
        """Rotate the component by the specified degrees keeping the anchor fixed on the grid."""
        # Store existing wire connections before rotation
        old_connections = []
        for point in self.connection_points:
            for wire in point.connected_wires[:]:  # Copy list to avoid modification during iteration
                if hasattr(wire, 'start_point') and wire.start_point == point:
                    old_connections.append((wire, 'start', point.point_id))
                elif hasattr(wire, 'end_point') and wire.end_point == point:
                    old_connections.append((wire, 'end', point.point_id))

        # Record anchor scene position BEFORE rotation
        old_anchor_scene = self.mapToScene(self.get_anchor_local_pos())

        # Update orientation (normalize to 0,90,180,270)
        self.orientation = (self.orientation + degrees) % 360

        # Update transform origin (may change due to orientation affecting effective dimensions)
        self.update_transform_origin()

        # Apply rotation about anchor
        self.setRotation(self.orientation)

        # After rotation, compute new anchor scene position and compensate translation
        new_anchor_scene = self.mapToScene(self.get_anchor_local_pos())
        delta = old_anchor_scene - new_anchor_scene
        if abs(delta.x()) > 0.01 or abs(delta.y()) > 0.01:
            # Move so anchor stays where it was
            self.setPos(self.pos() + delta)

        # Recreate connection points with new positions
        self.remove_connection_points()
        self.create_connection_points()

        # Reconnect wires to the new connection points
        for wire, connection_type, old_point_id in old_connections:
            new_point = None
            for point in self.connection_points:
                if point.point_id == old_point_id:
                    new_point = point
                    break
            if new_point:
                if connection_type == 'start':
                    wire.start_point = new_point
                elif connection_type == 'end':
                    wire.end_point = new_point
                new_point.connected_wires.append(wire)
                wire.update_position()

        # Snap again (keeps anchor aligned to grid rule after rotation rounding errors)
        self.snap_to_grid()
        self.update_connected_wires()

        # Resolve any overlap caused by changed footprint
        scene = self.scene()
        if scene and scene.views():
            main_window = scene.views()[0].main_window
            if hasattr(main_window, 'check_position_conflict') and main_window.check_position_conflict(self):
                if hasattr(main_window, 'find_free_grid_position'):
                    free_pos = main_window.find_free_grid_position(self.get_display_grid_position(), self)
                    if free_pos:
                        gx, gy = free_pos
                        self.move_to_grid_position(gx, gy)
                        if hasattr(main_window, 'log_panel'):
                            main_window.log_panel.log_message(f"[WARN] Overlap na rotatie opgelost door verplaatsing naar {free_pos}")

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
                main_window.log_panel.log_message(f"[INFO] {self.name} rotated to {self.orientation}°")

    def remove_connection_points(self):
        """Remove existing connection points"""
        for point in self.connection_points:
            point.connected_wires.clear()
            if point.scene():
                point.scene().removeItem(point)
        self.connection_points.clear()

    def mousePressEvent(self, event):
        # Handle selection
        if event.button() == Qt.MouseButton.LeftButton:
            # Store position for undo/redo when dragging starts
            self._drag_start_pos = self.pos()

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
        """Handle item changes like selection and live position updates"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Item is being selected
                self.setPen(QPen(QColor(255, 0, 0), 3))
                self.setZValue(500)
            else:
                self.setPen(QPen(QColor(0, 0, 0), 2))
                self.setZValue(50)
        elif change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            # Live update inspect panel position if this component is selected
            if self.isSelected() and self.scene() and self.scene().views():
                main_window = self.scene().views()[0].main_window
                if hasattr(main_window, 'inspect_panel'):
                    main_window.inspect_panel.update_component_data(self)
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
        """Create connection points positioned so they land on grid junctions.
        Rules:
        - Resistor/Switch (2x1 cells): horizontal orientations (0/180) place both terminals at y=0 to align with a single grid row.
          Vertical orientations (90/270) already have mid_x = width/2 = grid multiple (since width=2*g) so remain.
        - Single-terminal components (1x1) remain at (0,0).
        """
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        mid_x = width / 2.0
        mid_y = height / 2.0
        self.connection_points = []
        if self.component_type in ["Resistor", "Switch"]:
            if self.orientation == 0:      # Horizontal (anchor at left, y=0 grid row)
                left_point = ConnectionPoint(self, 0, 0, "in")
                right_point = ConnectionPoint(self, width, 0, "out")
                self.connection_points.extend([left_point, right_point])
            elif self.orientation == 90:   # Vertical
                top_point = ConnectionPoint(self, mid_x, 0, "in")
                bottom_point = ConnectionPoint(self, mid_x, height, "out")
                self.connection_points.extend([top_point, bottom_point])
            elif self.orientation == 180:  # Horizontal flipped
                left_point = ConnectionPoint(self, width, 0, "in")
                right_point = ConnectionPoint(self, 0, 0, "out")
                self.connection_points.extend([left_point, right_point])
            else:  # 270 Vertical flipped
                top_point = ConnectionPoint(self, mid_x, height, "in")
                bottom_point = ConnectionPoint(self, mid_x, 0, "out")
                self.connection_points.extend([top_point, bottom_point])
        elif self.component_type in ["Vdc", "GND", "Light"]:
            terminal = ConnectionPoint(self, 0, 0, "terminal")
            self.connection_points.append(terminal)

    def mouseReleaseEvent(self, event):
        # Snap to grid when released (anchor logic)
        self.snap_to_grid()
        # Resolve conflicts after snapping
        if self.scene() and self.scene().views():
            main_window = self.scene().views()[0].main_window
            if hasattr(main_window, 'check_position_conflict') and main_window.check_position_conflict(self):
                # Attempt to relocate automatically
                if hasattr(main_window, 'find_free_grid_position'):
                    free_pos = main_window.find_free_grid_position(self.get_display_grid_position(), self)
                    if free_pos:
                        gx, gy = free_pos
                        self.move_to_grid_position(gx, gy)
                        if hasattr(main_window, 'log_panel'):
                            main_window.log_panel.log_message(f"[WARN] Component moved to free grid point {free_pos} to avoid overlap")

            # Create undo command if position changed
            if hasattr(self, '_drag_start_pos') and self._drag_start_pos is not None:
                new_pos = self.pos()
                # Check if position actually changed (tolerance for floating point)
                if (abs(new_pos.x() - self._drag_start_pos.x()) > 0.1 or
                    abs(new_pos.y() - self._drag_start_pos.y()) > 0.1):
                    # Create move command
                    if hasattr(main_window, 'undo_stack'):
                        from ui.undo_commands import MoveComponentCommand
                        command = MoveComponentCommand(
                            self,
                            self._drag_start_pos,
                            new_pos,
                            f"Move {self.component_type}"
                        )
                        main_window.undo_stack.push(command)
                # Clear stored position
                self._drag_start_pos = None

        # Update all connected wires
        self.update_connected_wires()
        super().mouseReleaseEvent(event)

    def snap_to_grid(self):
        """Snap anchor (dynamic per component) to nearest grid junction.
        Keeps full footprint inside grid bounds. After moving anchor, apply a single global
        correction so at least one connection point is perfectly on-grid. This guarantees both
        logical junction alignment for backend and consistent visual placement.
        """
        if not self.scene():
            return
        views = self.scene().views()
        if not views:
            return
        view = views[0]
        g = self.grid_spacing
        anchor_local = self.get_anchor_local_pos()
        anchor_scene = self.mapToScene(anchor_local)
        # Compute snapped anchor target
        snapped_x = round(anchor_scene.x() / g) * g
        snapped_y = round(anchor_scene.y() / g) * g
        # Clamp within grid
        if hasattr(view, 'grid_rect') and view.grid_rect:
            grid_left, grid_top, grid_w, grid_h = view.grid_rect
            grid_right = grid_left + grid_w
            grid_bottom = grid_top + grid_h
            eff_w_cells, eff_h_cells = self.compute_effective_cell_dimensions()
            comp_w = eff_w_cells * g
            comp_h = eff_h_cells * g
            # Determine tentative top-left of component given desired anchor position.
            # We need to know how anchor_local relates to top-left (0,0) of rect.
            # So delta_local = anchor_local - (0,0) = anchor_local.
            # Top-left scene if anchor at (snapped_x, snapped_y) becomes (snapped_x - anchor_local.x(), snapped_y - anchor_local.y())
            top_left_x = snapped_x - anchor_local.x()
            top_left_y = snapped_y - anchor_local.y()
            # Clamp top-left so full rect inside bounds
            min_top_left_x = grid_left
            max_top_left_x = grid_right - comp_w
            min_top_left_y = grid_top
            max_top_left_y = grid_bottom - comp_h
            clamped_top_left_x = max(min_top_left_x, min(max_top_left_x, top_left_x))
            clamped_top_left_y = max(min_top_left_y, min(max_top_left_y, top_left_y))
            # Recalculate anchor target if we had to clamp
            snapped_x = clamped_top_left_x + anchor_local.x()
            snapped_y = clamped_top_left_y + anchor_local.y()
        # Apply translation
        delta_x = snapped_x - anchor_scene.x()
        delta_y = snapped_y - anchor_scene.y()
        if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
            self.setPos(self.pos() + QPointF(delta_x, delta_y))
        # Final minor correction based on first connection point if any
        if self.connection_points:
            first_cp = self.connection_points[0]
            cp_scene = first_cp.get_scene_pos()
            target_x = round(cp_scene.x() / g) * g
            target_y = round(cp_scene.y() / g) * g
            adjust = QPointF(target_x - cp_scene.x(), target_y - cp_scene.y())
            if abs(adjust.x()) > 0.01 or abs(adjust.y()) > 0.01:
                self.setPos(self.pos() + adjust)

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

        if self.component_type == "Resistor":
            return self.create_resistor_icon(width, height)
        elif self.component_type == "Vdc":
            return self.create_vdc_icon(width, height)
        elif self.component_type == "GND":
            return self.create_ground_icon(width, height)
        elif self.component_type == "Switch":
            return self.create_switch_icon(width, height)
        elif self.component_type == "Light":
            return self.create_light_icon(width, height)
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

    def create_switch_icon(self, width, height):
        """Create a switch icon (line with a break/gap)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_y = height / 2
        gap_size = width / 8
        switch_length = width / 3

        # Draw left terminal line
        painter.drawLine(QPointF(0, center_y),
                        QPointF(width/2 - gap_size, center_y))

        # Draw switch lever (angled line for open switch)
        lever_start = QPointF(width/2 - gap_size, center_y)
        lever_end = QPointF(width/2 + gap_size, center_y - height/4)
        painter.drawLine(lever_start, lever_end)

        # Draw small circle at lever pivot
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(lever_start, 2, 2)

        # Draw right terminal line
        painter.drawLine(QPointF(width/2 + gap_size, center_y),
                        QPointF(width, center_y))

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def create_light_icon(self, width, height):
        """Create a light bulb icon (circle with filament and rays)"""
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        center_x = width / 2
        center_y = height / 2

        # Draw circle (bulb)
        radius = min(width, height) / 3
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # Draw filament (X inside)
        filament_size = radius / 2
        painter.drawLine(QPointF(center_x - filament_size, center_y - filament_size),
                        QPointF(center_x + filament_size, center_y + filament_size))
        painter.drawLine(QPointF(center_x + filament_size, center_y - filament_size),
                        QPointF(center_x - filament_size, center_y + filament_size))

        # Draw light rays (4 small lines around the circle)
        ray_length = radius / 3
        ray_distance = radius + 2
        pen.setWidth(1)
        painter.setPen(pen)

        # Top ray
        painter.drawLine(QPointF(center_x, center_y - ray_distance),
                        QPointF(center_x, center_y - ray_distance - ray_length))
        # Bottom ray
        painter.drawLine(QPointF(center_x, center_y + ray_distance),
                        QPointF(center_x, center_y + ray_distance + ray_length))
        # Left ray
        painter.drawLine(QPointF(center_x - ray_distance, center_y),
                        QPointF(center_x - ray_distance - ray_length, center_y))
        # Right ray
        painter.drawLine(QPointF(center_x + ray_distance, center_y),
                        QPointF(center_x + ray_distance + ray_length, center_y))

        painter.end()

        icon_item = QGraphicsPixmapItem(pixmap)
        icon_item.setPos(0, 0)
        return icon_item

    def get_display_grid_position(self):
        """Return integer grid indices (gx, gy) of the anchor (dynamic per component)."""
        if not self.scene() or not self.scene().views():
            return 0, 0
        g = self.grid_spacing
        anchor_scene = self.mapToScene(self.get_anchor_local_pos())
        return int(round(anchor_scene.x() / g)), int(round(anchor_scene.y() / g))

    def move_to_grid_position(self, gx, gy):
        """Reposition component so its display grid position (center) becomes (gx, gy).
        Keeps rotation & anchor logic intact, then reapplies snapping and wire updates."""
        if not self.scene() or not self.scene().views():
            return
        g = self.grid_spacing
        target_center = QPointF(gx * g, gy * g)
        current_center = self.mapToScene(self.get_anchor_local_pos())
        delta = target_center - current_center
        if abs(delta.x()) > 0.01 or abs(delta.y()) > 0.01:
            self.setPos(self.pos() + delta)
        # Finalize with grid snap to enforce anchor/grid alignment and adjust minor errors
        self.snap_to_grid()
        self.update_connected_wires()

    def get_occupied_grid_cells(self, base_gx=None, base_gy=None):
        """Return a set of (gx, gy) cells occupied by this component based on its orientation.
        If base_gx/base_gy provided, treat that as anchor grid coordinate instead of current.
        Anchor grid coordinate corresponds to get_display_grid_position().
        Horizontal (eff_w >= eff_h) extends along +x; vertical along +y."""
        gx, gy = self.get_display_grid_position()
        if base_gx is not None and base_gy is not None:
            gx, gy = base_gx, base_gy
        eff_w, eff_h = self.compute_effective_cell_dimensions()
        cells = set()
        if eff_w >= eff_h:  # treat as horizontal footprint
            for dx in range(eff_w):
                cells.add((gx + dx, gy))
        else:  # vertical footprint
            for dy in range(eff_h):
                cells.add((gx, gy + dy))
        return cells
