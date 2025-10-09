from PyQt6.QtWidgets import QToolBar
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence


class ToolbarManager(QObject):
    """Manages the main toolbar and keyboard shortcuts"""

    # Signals for toolbar actions
    new_requested = pyqtSignal()
    open_requested = pyqtSignal()
    save_requested = pyqtSignal()
    run_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    # Additional action signals
    copy_output_requested = pyqtSignal()
    select_all_requested = pyqtSignal()
    deselect_all_requested = pyqtSignal()
    focus_canvas_requested = pyqtSignal()
    clear_log_requested = pyqtSignal()
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_reset_requested = pyqtSignal()
    center_view_requested = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.toolbar = None
        self.setup_toolbar()
        self.setup_additional_shortcuts()

    def setup_toolbar(self):
        """Setup the main toolbar"""
        self.toolbar = QToolBar("mainToolBar")
        self.main_window.addToolBar(self.toolbar)

        # Create toolbar actions with keyboard shortcuts
        self.actionNieuw = QAction("New", self.main_window)
        self.actionNieuw.setShortcut(QKeySequence.StandardKey.New)
        self.actionNieuw.setToolTip("New project (Ctrl+N)")

        self.actionOpenen = QAction("Open", self.main_window)
        self.actionOpenen.setShortcut(QKeySequence.StandardKey.Open)
        self.actionOpenen.setToolTip("Open project (Ctrl+O)")

        self.actionOpslaan = QAction("Save", self.main_window)
        self.actionOpslaan.setShortcut(QKeySequence.StandardKey.Save)
        self.actionOpslaan.setToolTip("Save project (Ctrl+S)")

        self.actionRun = QAction("Run", self.main_window)
        self.actionRun.setShortcut(QKeySequence("F5"))
        self.actionRun.setToolTip("Start simulation (F5)")

        self.actionStop = QAction("Stop", self.main_window)
        self.actionStop.setShortcut(QKeySequence("Shift+F5"))
        self.actionStop.setToolTip("Stop simulation (Shift+F5)")

        # Add actions to toolbar
        self.toolbar.addAction(self.actionNieuw)
        self.toolbar.addAction(self.actionOpenen)
        self.toolbar.addAction(self.actionOpslaan)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionRun)
        self.toolbar.addAction(self.actionStop)

        # Connect actions to signals
        self.actionNieuw.triggered.connect(self.new_requested.emit)
        self.actionOpenen.triggered.connect(self.open_requested.emit)
        self.actionOpslaan.triggered.connect(self.save_requested.emit)
        self.actionRun.triggered.connect(self.run_requested.emit)
        self.actionStop.triggered.connect(self.stop_requested.emit)

    def setup_additional_shortcuts(self):
        """Setup additional keyboard shortcuts"""
        # Copy output shortcut
        self.actionCopyOutput = QAction("Copy Output", self.main_window)
        self.actionCopyOutput.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.actionCopyOutput.triggered.connect(self.copy_output_requested.emit)
        self.main_window.addAction(self.actionCopyOutput)

        # Select All shortcut
        self.actionSelectAll = QAction("Select All", self.main_window)
        self.actionSelectAll.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.actionSelectAll.triggered.connect(self.select_all_requested.emit)
        self.main_window.addAction(self.actionSelectAll)

        # Deselect All shortcut
        self.actionDeselectAll = QAction("Deselect All", self.main_window)
        self.actionDeselectAll.setShortcut(QKeySequence("Ctrl+D"))
        self.actionDeselectAll.triggered.connect(self.deselect_all_requested.emit)
        self.main_window.addAction(self.actionDeselectAll)

        # Focus shortcuts
        self.actionFocusCanvas = QAction("Focus Canvas", self.main_window)
        self.actionFocusCanvas.setShortcut(QKeySequence("F1"))
        self.actionFocusCanvas.triggered.connect(self.focus_canvas_requested.emit)
        self.main_window.addAction(self.actionFocusCanvas)

        # Clear log shortcut
        self.actionClearLog = QAction("Clear Log", self.main_window)
        self.actionClearLog.setShortcut(QKeySequence("Ctrl+L"))
        self.actionClearLog.triggered.connect(self.clear_log_requested.emit)
        self.main_window.addAction(self.actionClearLog)

        # Zoom shortcuts
        self.actionZoomIn = QAction("Zoom In", self.main_window)
        self.actionZoomIn.setShortcut(QKeySequence("Ctrl++"))
        self.actionZoomIn.triggered.connect(self.zoom_in_requested.emit)
        self.main_window.addAction(self.actionZoomIn)

        self.actionZoomOut = QAction("Zoom Out", self.main_window)
        self.actionZoomOut.setShortcut(QKeySequence("Ctrl+-"))
        self.actionZoomOut.triggered.connect(self.zoom_out_requested.emit)
        self.main_window.addAction(self.actionZoomOut)

        self.actionZoomReset = QAction("Reset Zoom", self.main_window)
        self.actionZoomReset.setShortcut(QKeySequence("Ctrl+0"))
        self.actionZoomReset.triggered.connect(self.zoom_reset_requested.emit)
        self.main_window.addAction(self.actionZoomReset)

        # Center view shortcut
        self.actionCenterView = QAction("Center View", self.main_window)
        self.actionCenterView.setShortcut(QKeySequence("Home"))
        self.actionCenterView.triggered.connect(self.center_view_requested.emit)
        self.main_window.addAction(self.actionCenterView)
