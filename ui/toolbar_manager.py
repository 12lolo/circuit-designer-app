from PyQt6.QtWidgets import QToolBar
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from ui.quick_access_toolbar import QuickAccessToolbar


class ToolbarManager(QObject):
    """Manages the main toolbar and keyboard shortcuts"""

    # Signals for toolbar actions
    new_requested = pyqtSignal()
    open_requested = pyqtSignal()
    save_requested = pyqtSignal()
    save_copy_requested = pyqtSignal()
    run_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    # Additional action signals
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    paste_requested = pyqtSignal()
    copy_output_requested = pyqtSignal()
    select_all_requested = pyqtSignal()
    deselect_all_requested = pyqtSignal()
    focus_canvas_requested = pyqtSignal()
    clear_log_requested = pyqtSignal()
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_reset_requested = pyqtSignal()
    center_view_requested = pyqtSignal()
    export_png_requested = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.toolbar = None
        self.setup_toolbar()
        self.setup_additional_shortcuts()

    def setup_toolbar(self):
        """Setup the quick access toolbar"""
        self.toolbar = QuickAccessToolbar()
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

        self.actionSaveCopy = QAction("Save Copy", self.main_window)
        self.actionSaveCopy.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.actionSaveCopy.setToolTip("Save a copy to any location (Ctrl+Shift+S)")

        self.actionRun = QAction("Run", self.main_window)
        self.actionRun.setShortcut(QKeySequence("F5"))
        self.actionRun.setToolTip("Start simulation (F5)")

        self.actionStop = QAction("Stop", self.main_window)
        self.actionStop.setShortcut(QKeySequence("Shift+F5"))
        self.actionStop.setToolTip("Stop simulation (Shift+F5)")

        # Undo/Redo actions
        self.actionUndo = QAction("Undo", self.main_window)
        self.actionUndo.setShortcut(QKeySequence.StandardKey.Undo)
        self.actionUndo.setToolTip("Undo last action (Ctrl+Z)")

        self.actionRedo = QAction("Redo", self.main_window)
        self.actionRedo.setShortcut(QKeySequence.StandardKey.Redo)
        self.actionRedo.setToolTip("Redo last undone action (Ctrl+Shift+Z)")

        # Connect actions to signals
        self.actionNieuw.triggered.connect(self.new_requested.emit)
        self.actionOpenen.triggered.connect(self.open_requested.emit)
        self.actionOpslaan.triggered.connect(self.save_requested.emit)
        self.actionSaveCopy.triggered.connect(self.save_copy_requested.emit)
        self.actionUndo.triggered.connect(self.undo_requested.emit)
        self.actionRedo.triggered.connect(self.redo_requested.emit)
        self.actionRun.triggered.connect(self.run_requested.emit)
        self.actionStop.triggered.connect(self.stop_requested.emit)

        # Register actions with quick access toolbar
        # Default pinned: New, Open, Save, Run, Undo, Redo
        self.toolbar.register_action(self.actionNieuw, "New")
        self.toolbar.register_action(self.actionOpenen, "Open")
        self.toolbar.register_action(self.actionOpslaan, "Save")
        self.toolbar.register_action(self.actionSaveCopy, "Save Copy")
        self.toolbar.register_action(self.actionUndo, "Undo")
        self.toolbar.register_action(self.actionRedo, "Redo")
        self.toolbar.register_action(self.actionRun, "Run")
        self.toolbar.register_action(self.actionStop, "Stop")

    def setup_additional_shortcuts(self):
        """Setup additional keyboard shortcuts"""
        # Copy/Paste shortcuts
        self.actionCopy = QAction("Copy", self.main_window)
        self.actionCopy.setShortcut(QKeySequence.StandardKey.Copy)
        self.actionCopy.triggered.connect(self.copy_requested.emit)
        self.main_window.addAction(self.actionCopy)

        self.actionPaste = QAction("Paste", self.main_window)
        self.actionPaste.setShortcut(QKeySequence.StandardKey.Paste)
        self.actionPaste.triggered.connect(self.paste_requested.emit)
        self.main_window.addAction(self.actionPaste)

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
        self.actionZoomIn.setShortcut(QKeySequence("Ctrl+="))
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

        # Export PNG shortcut
        self.actionExportPNG = QAction("Export as PNG", self.main_window)
        self.actionExportPNG.setShortcut(QKeySequence("Ctrl+E"))
        self.actionExportPNG.triggered.connect(self.export_png_requested.emit)
        self.main_window.addAction(self.actionExportPNG)

        # Register all additional actions with quick access toolbar (not pinned by default)
        self.toolbar.register_action(self.actionCopy, "Copy")
        self.toolbar.register_action(self.actionPaste, "Paste")
        self.toolbar.register_action(self.actionCopyOutput, "Copy Output")
        self.toolbar.register_action(self.actionSelectAll, "Select All")
        self.toolbar.register_action(self.actionDeselectAll, "Deselect All")
        self.toolbar.register_action(self.actionFocusCanvas, "Focus Canvas")
        self.toolbar.register_action(self.actionClearLog, "Clear Log")
        self.toolbar.register_action(self.actionZoomIn, "Zoom In")
        self.toolbar.register_action(self.actionZoomOut, "Zoom Out")
        self.toolbar.register_action(self.actionZoomReset, "Reset Zoom")
        self.toolbar.register_action(self.actionCenterView, "Center View")
        self.toolbar.register_action(self.actionExportPNG, "Export PNG")
