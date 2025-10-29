"""Canvas Manager - Handles viewport, zoom, grid, and view operations"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush


class CanvasManager:
    """Manages canvas viewport, zoom, grid drawing, and view operations"""

    def __init__(self, graphics_view, scene, log_panel):
        """
        Initialize CanvasManager

        Args:
            graphics_view: The QGraphicsView (DroppableGraphicsView)
            scene: The QGraphicsScene
            log_panel: LogPanel for logging messages
        """
        self.graphics_view = graphics_view
        self.scene = scene
        self.log_panel = log_panel
        self.floating_controls = None

    def draw_grid(self):
        """Draw the grid on the graphics scene with an outer non-placeable border.
        Visual grid: (placement_cells + 2) cells per side (adds 1 cell border on each side).
        Placement grid (where components may snap/occupy): placement_cells per side (original 15).
        Components are clamped to placement grid via graphicsViewSandbox.grid_rect.
        """
        # Configuration
        placement_cells = 15
        border_thickness_cells = 1  # one cell each side
        visual_cells = placement_cells + 2 * border_thickness_cells

        # Base scene dimension previously 1000x600 leading to blank space; derive spacing from a square target height
        # Keep same spacing logic so internal cell size stable relative to previous behavior.
        target_height = 600  # legacy vertical dimension baseline
        grid_spacing = target_height / placement_cells  # cell size

        # Dimensions
        placement_width = placement_cells * grid_spacing
        placement_height = placement_cells * grid_spacing
        visual_width = visual_cells * grid_spacing
        visual_height = visual_cells * grid_spacing

        # Offsets (centered at origin). Placement rect inset by 1 cell within visual rect
        placement_left = -placement_width / 2
        placement_top = -placement_height / 2
        visual_left = -visual_width / 2
        visual_top = -visual_height / 2

        # Clear ONLY previous grid lines (keep components if re-drawing). Detect by custom data flag.
        for item in self.scene.items():
            try:
                if hasattr(item, 'data') and item.data(0) in ('grid', 'grid-border'):
                    self.scene.removeItem(item)
            except Exception:
                pass

        # Update graphics view spacing
        self.graphics_view.grid_spacing = grid_spacing

        # Store placement bounds for snapping/clamping (used by components)
        self.graphics_view.grid_rect = (placement_left, placement_top, placement_width, placement_height)
        # Store visual bounds (for potential future use like centering, limiting panning)
        self.graphics_view.visual_grid_rect = (visual_left, visual_top, visual_width, visual_height)

        # Shrink scene rect to visual grid (minimal blank area)
        self.scene.setSceneRect(visual_left, visual_top, visual_width, visual_height)

        light_pen = QPen(QColor(220, 220, 220))
        inner_border_pen = QPen(QColor(180, 180, 180))
        outer_border_pen = QPen(QColor(80, 80, 80), 2)

        # Helper to add line with tag
        def add_line(x1, y1, x2, y2, pen):
            line_item = self.scene.addLine(x1, y1, x2, y2, pen)
            try:
                line_item.setData(0, 'grid')
            except Exception:
                pass

        # Draw full visual grid lines
        for i in range(visual_cells + 1):  # lines count = cells + 1
            x = visual_left + i * grid_spacing
            pen = light_pen
            # Vertical outer border
            if i == 0 or i == visual_cells:
                pen = outer_border_pen
            # Placement border (inner ring) thicker/darker than inner lines
            elif i == border_thickness_cells or i == visual_cells - border_thickness_cells:
                pen = inner_border_pen
            add_line(x, visual_top, x, visual_top + visual_height, pen)

        for i in range(visual_cells + 1):
            y = visual_top + i * grid_spacing
            pen = light_pen
            if i == 0 or i == visual_cells:
                pen = outer_border_pen
            elif i == border_thickness_cells or i == visual_cells - border_thickness_cells:
                pen = inner_border_pen
            add_line(visual_left, y, visual_left + visual_width, y, pen)

        # Add shaded forbidden border rectangles
        shaded_brush = QBrush(QColor(50, 50, 50, 40))
        def add_shaded_rect(x, y, w, h):
            rect_item = QGraphicsRectItem(x, y, w, h)
            rect_item.setBrush(shaded_brush)
            rect_item.setPen(QPen(Qt.PenStyle.NoPen))
            rect_item.setZValue(-10)  # behind grid lines
            rect_item.setData(0, 'grid-border')
            self.scene.addItem(rect_item)
        # Left border
        add_shaded_rect(visual_left, visual_top, grid_spacing, visual_height)
        # Right border
        add_shaded_rect(placement_left + placement_width, visual_top, grid_spacing, visual_height)
        # Top border
        add_shaded_rect(visual_left + grid_spacing, visual_top, placement_width, grid_spacing)
        # Bottom border
        add_shaded_rect(visual_left + grid_spacing, placement_top + placement_height, placement_width, grid_spacing)

        # Center view on grid after redraw
        self.graphics_view.centerOn(0, 0)
        # Enforce new min zoom immediately
        if hasattr(self.graphics_view, 'update_min_zoom'):
            self.graphics_view.update_min_zoom()

    def zoom_in(self):
        """Zoom in on the canvas"""
        self.graphics_view.scale(1.2, 1.2)

    def zoom_out(self):
        """Zoom out on the canvas"""
        self.graphics_view.scale(0.8, 0.8)

    def zoom_reset(self):
        """Reset zoom to 1:1"""
        self.graphics_view.resetTransform()
        # Enforce min zoom and clamp to grid after reset
        if hasattr(self.graphics_view, 'update_min_zoom'):
            self.graphics_view.update_min_zoom()
        if hasattr(self.graphics_view, 'clamp_view_to_visual_grid'):
            self.graphics_view.clamp_view_to_visual_grid()

    def center_view(self):
        """Center the view on the scene"""
        self.graphics_view.centerOn(0, 0)
        self.log_panel.log_message("[INFO] View centered")

    def position_floating_controls(self):
        """Place floating controls at a corner inside the canvas viewport, based on its current anchor."""
        if self.floating_controls is None:
            return
        try:
            # Prefer anchor-based repositioning if available (draggable snapping)
            if hasattr(self.floating_controls, 'reposition_to_anchor'):
                # Ensure size hint is realized before computing anchor positions
                self.floating_controls.adjustSize()
                self.floating_controls.reposition_to_anchor()
                return
        except Exception:
            pass
        # Fallback: top-left margin
        margin_x = 10
        margin_y = 10
        self.floating_controls.adjustSize()
        self.floating_controls.move(margin_x, margin_y)
        self.floating_controls.raise_()
        self.floating_controls.show()

    def set_floating_controls(self, floating_controls):
        """Set the floating controls widget"""
        self.floating_controls = floating_controls
