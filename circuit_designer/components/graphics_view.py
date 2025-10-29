"""
Graphics view for ECis-full application.
Handles the droppable graphics view for circuit components.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QKeySequence

try:
    from .component_item import ComponentItem
except ImportError:  # Allow running this file directly (no package context)
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from circuit_designer.components.component_item import ComponentItem


class DroppableGraphicsView(QGraphicsView):
    """Custom graphics view that accepts drops"""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.grid_spacing = 40  # Will be updated when grid is drawn
        self.grid_rect = None   # (x, y, w, h) stored by main_window.drawGrid

        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set up zoom parameters
        self.zoom_factor = 1.15
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        self.current_zoom = 1.0

        # Stable zoom behavior
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def clamp_view_to_visual_grid(self):
        """Clamp the view center so the visual grid always fills the viewport without exposing large blank areas.
        Works in scene coordinates using current transform scale.
        """
        if not hasattr(self, 'visual_grid_rect') or self.visual_grid_rect is None:
            return
        v_left, v_top, v_w, v_h = self.visual_grid_rect
        scale = self.transform().m11() or 1.0
        # Visible extents in scene units
        half_vis_w = (self.viewport().width() / scale) / 2.0
        half_vis_h = (self.viewport().height() / scale) / 2.0
        min_cx = v_left + half_vis_w
        max_cx = v_left + v_w - half_vis_w
        min_cy = v_top + half_vis_h
        max_cy = v_top + v_h - half_vis_h
        # If viewport bigger than grid dimension, pin to center
        if min_cx > max_cx:
            min_cx = max_cx = v_left + v_w / 2.0
        if min_cy > max_cy:
            min_cy = max_cy = v_top + v_h / 2.0
        current_center = self.mapToScene(self.viewport().rect().center())
        cx = current_center.x()
        cy = current_center.y()
        clamped_cx = max(min_cx, min(max_cx, cx))
        clamped_cy = max(min_cy, min(max_cy, cy))
        if abs(clamped_cx - cx) > 0.01 or abs(clamped_cy - cy) > 0.01:
            self.centerOn(clamped_cx, clamped_cy)

    def update_min_zoom(self):
        """Recalculate the minimum allowed zoom so that the visual grid fills (or slightly overfills) the viewport.
        Ensures user cannot zoom out so far that large empty space surrounds the raster.
        Requires self.visual_grid_rect (set by MainWindow.drawGrid)."""
        if not hasattr(self, 'visual_grid_rect') or self.visual_grid_rect is None:
            return
        v_left, v_top, v_w, v_h = self.visual_grid_rect
        grid_w = v_w
        grid_h = v_h
        vp_w = max(1, self.viewport().width())
        vp_h = max(1, self.viewport().height())
        scale_min_w = vp_w / grid_w
        scale_min_h = vp_h / grid_h
        min_scale = max(scale_min_w, scale_min_h)
        self.zoom_min = min_scale
        current_scale = self.transform().m11()
        self.current_zoom = current_scale
        if current_scale < min_scale * 0.999:
            factor = min_scale / current_scale
            self.scale(factor, factor)
            self.current_zoom = min_scale
        self.clamp_view_to_visual_grid()

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

                # Create component instance
                from .component_item import ComponentItem
                component = ComponentItem(component_type, size_w, size_h, self.grid_spacing)

                # Convert drop position to scene coordinates
                scene_pos = self.mapToScene(event.position().toPoint())

                # Place so that anchor local aligns with drop point (anchor determined dynamically)
                anchor_local = component.get_anchor_local_pos()
                component.setPos(scene_pos - anchor_local)

                # Resolve conflicts (prevent duplicate grid coordinate)
                main_window = self.main_window
                should_add = True

                # Add component through undo stack for undo/redo support (must be in scene before snap_to_grid)
                if should_add and hasattr(main_window, 'undo_stack'):
                    from circuit_designer.project.undo_commands import AddComponentCommand
                    command = AddComponentCommand(self.scene(), component, f"Add {component.component_type}")
                    main_window.undo_stack.push(command)
                else:
                    # Fallback if undo stack not available
                    self.scene().addItem(component)

                # NOW snap to grid (component must be in scene for this to work)
                component.snap_to_grid()

                # Check for conflicts after snapping
                if hasattr(main_window, 'check_position_conflict') and main_window.check_position_conflict(component):
                    if hasattr(main_window, 'find_free_grid_position'):
                        free_pos = main_window.find_free_grid_position(component.get_display_grid_position(), component)
                        if free_pos:
                            gx, gy = free_pos
                            component.move_to_grid_position(gx, gy)
                        else:
                            # Remove component if no free spot
                            self.scene().removeItem(component)
                            should_add = False
                            if hasattr(main_window, 'log_panel'):
                                main_window.log_panel.log_message("[WARN] No free position available for component placement")
                            event.acceptProposedAction()
                            return

                # Auto-select the newly dropped component
                if should_add:
                    component.setSelected(True)
                    if hasattr(main_window, 'on_component_selected'):
                        main_window.on_component_selected(component)

                if hasattr(main_window, 'log_panel'):
                    main_window.log_panel.log_message(f"[INFO] Component placed at grid {component.get_display_grid_position()}")

            event.acceptProposedAction()
        else:
            super().dropEvent(event)
        # After any drop, ensure min zoom still valid
        self.update_min_zoom()
        self.clamp_view_to_visual_grid()

    def wheelEvent(self, event):
        """Handle mouse wheel events: scroll up/down, Ctrl+scroll for zoom."""
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+scroll: zoom in/out (AnchorUnderMouse keeps cursor position stable)
            dy = event.angleDelta().y()
            if dy == 0 and hasattr(event, 'pixelDelta'):
                dy = event.pixelDelta().y()
            if dy != 0:
                # Compute desired zoom factor
                zoom_in = dy > 0
                base_factor = self.zoom_factor if zoom_in else (1.0 / self.zoom_factor)
                current_scale = self.transform().m11() or 1.0
                # Compute dynamic min scale from visual grid and viewport
                min_scale = 0.0
                if hasattr(self, 'visual_grid_rect') and self.visual_grid_rect is not None:
                    v_left, v_top, v_w, v_h = self.visual_grid_rect
                    vp_w = max(1, self.viewport().width())
                    vp_h = max(1, self.viewport().height())
                    min_scale = max(vp_w / max(1e-6, v_w), vp_h / max(1e-6, v_h))
                else:
                    min_scale = self.zoom_min
                # Clamp new scale between [min_scale, zoom_max]
                target_scale = current_scale * base_factor
                if target_scale < min_scale:
                    target_scale = min_scale
                if target_scale > self.zoom_max:
                    target_scale = self.zoom_max
                # Compute factor to apply
                apply_factor = target_scale / current_scale if current_scale > 0 else 1.0
                if abs(apply_factor - 1.0) > 1e-6:
                    self.scale(apply_factor, apply_factor)
                    self.current_zoom = target_scale
                event.accept()
            else:
                event.ignore()
            # Clamp after handling zoom
            self.clamp_view_to_visual_grid()
        else:
            # Default scrolling behavior
            super().wheelEvent(event)
            self.clamp_view_to_visual_grid()

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
        self.update_min_zoom()
        if self.current_zoom < self.zoom_max:
            zoom_factor = min(self.zoom_factor, self.zoom_max / self.current_zoom)
            self.scale(zoom_factor, zoom_factor)
            self.current_zoom *= zoom_factor
            self.clamp_view_to_visual_grid()

    def zoom_out(self):
        """Zoom out centered on viewport"""
        self.update_min_zoom()
        if self.current_zoom > self.zoom_min:
            zoom_factor = max(1.0 / self.zoom_factor, self.zoom_min / self.current_zoom)
            self.scale(zoom_factor, zoom_factor)
            self.current_zoom *= zoom_factor
            self.clamp_view_to_visual_grid()

    def reset_zoom(self):
        """Reset zoom to 100%"""
        zoom_factor = 1.0 / self.current_zoom
        self.scale(zoom_factor, zoom_factor)
        self.current_zoom = 1.0
        self.update_min_zoom()
        self.clamp_view_to_visual_grid()

    def center_view(self):
        """Center the view on the scene"""
        scene_rect = self.scene().itemsBoundingRect()
        if not scene_rect.isEmpty():
            self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.current_zoom = self.transform().m11()  # Get current scale
        else:
            # If no items, center on origin
            self.centerOn(0, 0)
        self.clamp_view_to_visual_grid()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Recompute min zoom on resize
        self.update_min_zoom()
        # Optionally recenter
        self.centerOn(0, 0)
        self.clamp_view_to_visual_grid()

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
        # Clamp after panning ends
        self.clamp_view_to_visual_grid()
