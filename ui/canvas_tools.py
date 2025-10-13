from PyQt6.QtWidgets import (
    QVBoxLayout, QToolButton, QSpacerItem, QSizePolicy, QWidget, QHBoxLayout, QStyle
)
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF


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

    # New floating controls API
    def get_floating_widget(self, parent: QWidget) -> QWidget:
        """Create (or return) a floating controls widget to overlay on the canvas.
        Order: Zoom In, Zoom Out, Clear, Run.
        """
        if self.floating_widget is not None:
            return self.floating_widget

        w = QWidget(parent)
        w.setObjectName("canvasFloatingControls")
        w.setStyleSheet(
            "#canvasFloatingControls {"
            "  background-color: rgba(40, 40, 40, 180);"
            "  border-radius: 8px;"
            "}"
        )
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
        fallback_clear = w.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        # Use a custom green play icon to satisfy the requirement
        fallback_run = self._make_green_play_icon()

        # Icons (theme with graceful fallbacks)
        zoom_in_icon = icon_from_theme("zoom-in", fallback_zoom_in)
        zoom_out_icon = icon_from_theme("zoom-out", fallback_zoom_out)
        clear_icon = icon_from_theme("user-trash", fallback_clear)
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
