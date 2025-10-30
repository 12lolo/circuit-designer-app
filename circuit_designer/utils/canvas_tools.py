from PyQt6.QtWidgets import (
    QVBoxLayout, QToolButton, QSpacerItem, QSizePolicy, QWidget, QHBoxLayout, QStyle
)
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF, Qt, QSize, QEvent
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF, QCursor


class CanvasTools(QObject):
    """Manages canvas interaction tools like zoom and probe"""

    # Signals for tool actions
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    probe_requested = pyqtSignal()
    # New: run and clear actions for floating controls
    run_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = None
        self.floating_widget = None
        self.setup_tools()

    def setup_tools(self):
        """Setup the canvas tools layout and buttons (legacy side layout)"""
        self.layout = QVBoxLayout()

        # Tool buttons (legacy vertical layout)
        self.btnZoomIn = QToolButton()
        self.btnZoomIn.setText("+")
        self.btnZoomIn.setToolTip("Zoom in")
        self.btnZoomIn.clicked.connect(self.zoom_in_requested.emit)

        self.btnZoomOut = QToolButton()
        self.btnZoomOut.setText("-")
        self.btnZoomOut.setToolTip("Zoom out")
        self.btnZoomOut.clicked.connect(self.zoom_out_requested.emit)

        # Keep probe button available for future use
        self.btnProbe = QToolButton()
        self.btnProbe.setText("→")
        self.btnProbe.setToolTip("Probe")
        self.btnProbe.clicked.connect(self.probe_requested.emit)

        # Add buttons to layout
        self.layout.addWidget(self.btnZoomIn)
        self.layout.addWidget(self.btnZoomOut)
        self.layout.addWidget(self.btnProbe)

        # Add spacer
        self.verticalSpacer_canvasTools = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.layout.addItem(self.verticalSpacer_canvasTools)

    def get_layout(self):
        """Get the layout containing all canvas tools (legacy sidebar)"""
        return self.layout

    def add_tool(self, text, tooltip, callback):
        """Add a custom tool button to the legacy layout"""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)

        # Insert before the spacer (last item)
        self.layout.insertWidget(self.layout.count() - 1, button)
        return button

    # Drawing helper for magnifier icons
    def _make_magnifier_icon(self, plus: bool) -> QIcon:
        size = 28
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Lens
        lens_rect = QRectF(5, 4, 16, 16)
        p.setPen(QPen(QColor(40, 40, 40), 2))
        p.setBrush(QColor(230, 230, 230))
        p.drawEllipse(lens_rect)

        # Handle
        p.setPen(QPen(QColor(40, 40, 40), 3))
        p.drawLine(QPointF(18, 17), QPointF(25, 24))

        # Plus/Minus glyph
        p.setPen(QPen(QColor(20, 20, 20), 2))
        # horizontal
        p.drawLine(QPointF(lens_rect.center().x() - 4, lens_rect.center().y()),
                   QPointF(lens_rect.center().x() + 4, lens_rect.center().y()))
        if plus:
            # vertical
            p.drawLine(QPointF(lens_rect.center().x(), lens_rect.center().y() - 4),
                       QPointF(lens_rect.center().x(), lens_rect.center().y() + 4))

        p.end()
        return QIcon(pm)

    def _make_green_play_icon(self) -> QIcon:
        size = 28
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Draw a right-pointing triangle
        tri = QPolygonF([
            QPointF(7, 5),
            QPointF(7, 23),
            QPointF(22, 14),
        ])
        p.setPen(QPen(QColor(20, 110, 50), 1.5))
        p.setBrush(QColor(39, 174, 96))  # green fill
        p.drawPolygon(tri)
        p.end()
        return QIcon(pm)

    def _make_trash_icon(self) -> QIcon:
        """Create a custom trash/delete icon that works well on Linux."""
        size = 22
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor(80, 80, 80), 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Draw trash can body (rectangle)
        p.drawRect(6, 9, 10, 10)
        # Draw lid (horizontal line)
        p.drawLine(4, 9, 18, 9)
        # Draw handle on lid
        p.drawLine(9, 6, 13, 6)
        p.drawLine(9, 6, 9, 9)
        p.drawLine(13, 6, 13, 9)
        # Draw vertical lines inside can
        p.drawLine(9, 11, 9, 17)
        p.drawLine(14, 11, 14, 17)

        p.end()
        return QIcon(pm)

    class FloatingControls(QWidget):
        """Draggable floating controls that snap to the nearest corner of parent viewport.
        The widget keeps an 'anchor' property: one of 'top-left', 'top-right', 'bottom-left', 'bottom-right'.
        """
        def __init__(self, parent: QWidget | None = None, margin: int = 10):
            super().__init__(parent)
            self.setObjectName("canvasFloatingControls")
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
            self.setMouseTracking(True)
            self._dragging = False
            self._drag_start_pos = QPointF()
            self._start_widget_pos = QPointF()
            self.anchor: str = 'top-left'
            self.margin: int = margin
            # Styling
            self.setStyleSheet(
                "#canvasFloatingControls {"
                "  background-color: rgba(40, 40, 40, 180);"
                "  border-radius: 8px;"
                "}"
            )
            # Track parent geometry updates so we always stay attached to the viewport edges
            if parent is not None:
                try:
                    parent.installEventFilter(self)
                except Exception:
                    pass
            # Ensure the widget stays on top
            self.raise_()

        def set_anchor(self, anchor: str):
            if anchor in ("top-left", "top-right", "bottom-left", "bottom-right"):
                self.anchor = anchor
                self.setProperty("anchor", anchor)

        def get_anchor(self) -> str:
            return getattr(self, 'anchor', 'top-left')

        def compute_anchor_pos(self) -> QPointF:
            parent = self.parentWidget()
            if not parent:
                return QPointF(0, 0)

            # If parent is a QGraphicsView, use viewport dimensions
            # Otherwise use parent dimensions
            try:
                from PyQt6.QtWidgets import QGraphicsView
                if isinstance(parent, QGraphicsView):
                    viewport = parent.viewport()
                    # Get viewport geometry relative to parent
                    viewport_rect = viewport.geometry()
                    parent_w = viewport_rect.width()
                    parent_h = viewport_rect.height()
                    offset_x = viewport_rect.x()
                    offset_y = viewport_rect.y()
                else:
                    parent_w = parent.width()
                    parent_h = parent.height()
                    offset_x = 0
                    offset_y = 0
            except:
                parent_w = parent.width()
                parent_h = parent.height()
                offset_x = 0
                offset_y = 0

            w = self.width()
            h = self.height()
            m = self.margin
            if self.anchor == 'top-left':
                return QPointF(offset_x + m, offset_y + m)
            if self.anchor == 'top-right':
                return QPointF(offset_x + parent_w - w - m, offset_y + m)
            if self.anchor == 'bottom-left':
                return QPointF(offset_x + m, offset_y + parent_h - h - m)
            # bottom-right default
            return QPointF(offset_x + parent_w - w - m, offset_y + parent_h - h - m)

        def reposition_to_anchor(self):
            pos = self.compute_anchor_pos()
            self.move(int(pos.x()), int(pos.y()))
            self.raise_()
            self.show()

        def _clamp_to_parent(self, x: int, y: int) -> tuple[int, int]:
            parent = self.parentWidget()
            if not parent:
                return x, y

            # If parent is a QGraphicsView, clamp to viewport area
            try:
                from PyQt6.QtWidgets import QGraphicsView
                if isinstance(parent, QGraphicsView):
                    viewport = parent.viewport()
                    viewport_rect = viewport.geometry()
                    max_x = max(viewport_rect.x(), viewport_rect.x() + viewport_rect.width() - self.width())
                    max_y = max(viewport_rect.y(), viewport_rect.y() + viewport_rect.height() - self.height())
                    min_x = viewport_rect.x()
                    min_y = viewport_rect.y()
                    return max(min_x, min(x, max_x)), max(min_y, min(y, max_y))
            except:
                pass

            # Default: clamp to parent bounds
            max_x = max(0, parent.width() - self.width())
            max_y = max(0, parent.height() - self.height())
            return max(0, min(x, max_x)), max(0, min(y, max_y))

        def set_overlay_parent(self, new_parent: QWidget | None):
            """Reparent the overlay to a new parent (e.g., a new viewport), reinstalling event filter and re-anchoring."""
            try:
                old_parent = self.parentWidget()
                if old_parent is new_parent:
                    return
                if old_parent is not None:
                    try:
                        old_parent.removeEventFilter(self)
                    except Exception:
                        pass
                self.setParent(new_parent)
                if new_parent is not None:
                    try:
                        new_parent.installEventFilter(self)
                    except Exception:
                        pass
                # Ensure geometry updated before reposition
                self.adjustSize()
                self.reposition_to_anchor()
            except Exception:
                pass

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                self._drag_start_pos = event.globalPosition()
                self._start_widget_pos = QPointF(self.x(), self.y())
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                event.accept()
                return
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if self._dragging:
                delta = event.globalPosition() - self._drag_start_pos
                new_x = int(self._start_widget_pos.x() + delta.x())
                new_y = int(self._start_widget_pos.y() + delta.y())
                new_x, new_y = self._clamp_to_parent(new_x, new_y)
                self.move(new_x, new_y)
                event.accept()
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            if self._dragging and event.button() == Qt.MouseButton.LeftButton:
                self._dragging = False
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
                # Snap to nearest corner of parent (or viewport if parent is QGraphicsView)
                parent = self.parentWidget()
                if parent:
                    # Get effective dimensions (viewport if QGraphicsView, else parent)
                    try:
                        from PyQt6.QtWidgets import QGraphicsView
                        if isinstance(parent, QGraphicsView):
                            viewport = parent.viewport()
                            viewport_rect = viewport.geometry()
                            offset_x = viewport_rect.x()
                            offset_y = viewport_rect.y()
                            parent_w = viewport_rect.width()
                            parent_h = viewport_rect.height()
                        else:
                            offset_x = 0
                            offset_y = 0
                            parent_w = parent.width()
                            parent_h = parent.height()
                    except:
                        offset_x = 0
                        offset_y = 0
                        parent_w = parent.width()
                        parent_h = parent.height()

                    corners = {
                        'top-left': QPointF(offset_x + self.margin, offset_y + self.margin),
                        'top-right': QPointF(offset_x + parent_w - self.width() - self.margin, offset_y + self.margin),
                        'bottom-left': QPointF(offset_x + self.margin, offset_y + parent_h - self.height() - self.margin),
                        'bottom-right': QPointF(offset_x + parent_w - self.width() - self.margin, offset_y + parent_h - self.height() - self.margin),
                    }
                    # compute distance from widget center to each corner target
                    center = QPointF(self.x() + self.width() / 2, self.y() + self.height() / 2)
                    def dist2(a: QPointF, b: QPointF) -> float:
                        dx = a.x() - b.x()
                        dy = a.y() - b.y()
                        return dx*dx + dy*dy
                    best_anchor = min(corners.keys(), key=lambda k: dist2(center, QPointF(corners[k].x() + self.width()/2, corners[k].y() + self.height()/2)))
                    self.set_anchor(best_anchor)
                    self.reposition_to_anchor()
                event.accept()
                return
            super().mouseReleaseEvent(event)

        def enterEvent(self, event):
            # Indicate draggability
            if not self._dragging:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            super().enterEvent(event)

        def leaveEvent(self, event):
            if not self._dragging:
                self.unsetCursor()
            super().leaveEvent(event)

        def paintEvent(self, event):
            """Override paint event to ensure widget stays visible and on top"""
            super().paintEvent(event)
            # Ensure we stay on top whenever repainted
            self.raise_()

        def eventFilter(self, watched, event):
            """Keep the overlay anchored to the viewport; react to parent geometry updates."""
            try:
                if watched is self.parentWidget():
                    if event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show, QEvent.Type.LayoutRequest):
                        self.reposition_to_anchor()
                        self.raise_()  # Ensure we stay on top
                return False
            except Exception:
                return False

    # New floating controls API
    def get_floating_widget(self, parent: QWidget) -> QWidget:
        """Create (or return) a floating controls widget to overlay on the canvas.
        Order: Zoom In, Zoom Out, Clear, Run.
        The widget is draggable and snaps to the nearest corner of the parent viewport.
        """
        if self.floating_widget is not None:
            # Ensure parent is correct (viewport); if changed, reparent and re-anchor
            if self.floating_widget.parentWidget() is not parent and hasattr(self.floating_widget, 'set_overlay_parent'):
                try:
                    self.floating_widget.set_overlay_parent(parent)
                except Exception:
                    self.floating_widget.setParent(parent)
            return self.floating_widget

        # Use the draggable snapping controls widget
        w = CanvasTools.FloatingControls(parent, margin=10)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Helpers
        def icon_from_theme(name: str, fallback_icon: QIcon | None = None) -> QIcon:
            ic = QIcon.fromTheme(name)
            if ic.isNull() and fallback_icon is not None:
                return fallback_icon
            return ic

        def make_btn(icon: QIcon, tooltip: str, clicked_cb, auto_raise=True, stylesheet: str | None = None):
            btn = QToolButton(w)
            btn.setAutoRaise(auto_raise)
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(tooltip)
            if stylesheet:
                btn.setStyleSheet(stylesheet)
            btn.clicked.connect(clicked_cb)
            return btn

        # Prepare fallbacks
        fallback_zoom_in = self._make_magnifier_icon(plus=True)
        fallback_zoom_out = self._make_magnifier_icon(plus=False)
        fallback_clear = self._make_trash_icon()
        # Use a custom green play icon to satisfy the requirement
        fallback_run = self._make_green_play_icon()

        # Icons (theme with graceful fallbacks)
        zoom_in_icon = icon_from_theme("zoom-in", fallback_zoom_in)
        zoom_out_icon = icon_from_theme("zoom-out", fallback_zoom_out)
        clear_icon = fallback_clear  # always use custom trash icon
        run_icon = fallback_run  # always use green play icon

        # Buttons: lens icons for zoom, trash for clear, green run (icon-only)
        btn_zoom_in = make_btn(zoom_in_icon, "Zoom in", self.zoom_in_requested.emit)
        btn_zoom_out = make_btn(zoom_out_icon, "Zoom out", self.zoom_out_requested.emit)
        btn_clear = make_btn(clear_icon, "Clear sandbox", self.clear_requested.emit)
        btn_run = make_btn(
            run_icon,
            "Run simulation",
            self.run_requested.emit,
            auto_raise=True,
            stylesheet=None,
        )

        # Add in order: zoom-in, zoom-out, clear, run
        layout.addWidget(btn_zoom_in)
        layout.addWidget(btn_zoom_out)
        layout.addWidget(btn_clear)
        layout.addWidget(btn_run)

        self.floating_widget = w
        return w
