import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QWidget, QLabel, QPushButton, QFrame, QMessageBox, QInputDialog, QMenu,
    QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor, QCursor
from typing import Optional, Dict


class ProjectCard(QFrame):
    """A card widget representing a single project"""

    clicked = pyqtSignal(object)  # Emits project data dict
    double_clicked = pyqtSignal(object)

    def __init__(self, project_data: Dict, parent=None, dialog=None):
        super().__init__(parent)
        self.project_data = project_data
        self.selected = False
        self.dialog = dialog  # Store reference to the dialog
        self.setupUi()

    def setupUi(self):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 280)  # Card size - slightly taller

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 8)  # Reduced margins
        layout.setSpacing(5)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(210, 210)  # Larger thumbnail
        self.thumbnail_label.setFrameStyle(QFrame.Shape.Box)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setScaledContents(True)  # Scale image to fill label

        # Load thumbnail
        if self.project_data.get('thumbnail'):
            self._load_thumbnail(self.project_data['thumbnail'])
        else:
            # Default placeholder
            self.thumbnail_label.setText("No Preview")
            self.thumbnail_label.setStyleSheet("background-color: #f0f0f0; color: #999;")

        layout.addWidget(self.thumbnail_label)

        # Project name
        name_label = QLabel(self.project_data['name'])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: black;")
        layout.addWidget(name_label)

        # Last modified time
        last_mod = self.project_data['last_modified']
        time_str = self._format_time(last_mod)
        time_label = QLabel(time_str)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet("color: #555; font-size: 8pt;")
        layout.addWidget(time_label)

        layout.addStretch()

        # Update visual state
        self._update_style()

    def _load_thumbnail(self, base64_str: str):
        """Load thumbnail from base64 string"""
        try:
            img_bytes = base64.b64decode(base64_str)
            image = QImage()
            image.loadFromData(img_bytes)

            pixmap = QPixmap.fromImage(image)
            # No need to scale - setScaledContents handles it
            self.thumbnail_label.setPixmap(pixmap)

        except Exception as e:
            print(f"Error loading thumbnail: {e}")
            self.thumbnail_label.setText("Invalid Preview")
            self.thumbnail_label.setStyleSheet("background-color: #ffe0e0; color: #c00;")

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for display"""
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"{mins} minute{'s' if mins != 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%b %d, %Y")

    def setSelected(self, selected: bool):
        """Set selection state"""
        self.selected = selected
        self._update_style()

    def _update_style(self):
        """Update card styling based on selection state"""
        if self.selected:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                ProjectCard {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                ProjectCard:hover {
                    background-color: #f5f5f5;
                    border: 1px solid #999;
                }
            """)

    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_data)
        elif event.button() == Qt.MouseButton.RightButton:
            # Let parent handle context menu
            pass
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.project_data)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu(self)

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.globalPos())

        if action == rename_action:
            self._handle_rename()
        elif action == delete_action:
            self._handle_delete()

    def _handle_rename(self):
        """Handle rename action"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Project",
            "Enter new name:",
            text=self.project_data['name']
        )

        if ok and new_name.strip():
            # Use dialog reference to handle renaming
            if self.dialog and hasattr(self.dialog, 'rename_project'):
                self.dialog.rename_project(self.project_data, new_name.strip())

    def _handle_delete(self):
        """Handle delete action"""
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete '{self.project_data['name']}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Use dialog reference to handle deletion
            if self.dialog and hasattr(self.dialog, 'delete_project'):
                self.dialog.delete_project(self.project_data)


class ProjectBrowserDialog(QDialog):
    """Dialog for browsing and selecting projects"""

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.selected_project = None
        self.project_cards = []
        self.all_projects = []  # Store all projects for filtering
        self.browsed_file = None  # Track file opened from file explorer
        self.setupUi()
        self.load_projects()

    def setupUi(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Open Project")
        self.setMinimumSize(950, 600)
        self.resize(950, 700)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Title
        title = QLabel("Select a Project")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        # Search and sort controls
        controls_layout = QHBoxLayout()

        # Search bar
        search_label = QLabel("Search:")
        controls_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to filter projects...")
        self.search_box.textChanged.connect(self.on_search_changed)
        self.search_box.setClearButtonEnabled(True)
        controls_layout.addWidget(self.search_box, 1)

        # Sort dropdown
        sort_label = QLabel("Sort by:")
        controls_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Last Modified (Newest)",
            "Last Modified (Oldest)",
            "Name (A-Z)",
            "Name (Z-A)"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        controls_layout.addWidget(self.sort_combo)

        main_layout.addLayout(controls_layout)

        # Scroll area for project grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll, 1)  # Stretch factor 1

        # Button bar
        button_layout = QHBoxLayout()

        # Browse button on the left
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setToolTip("Open file from another location")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        button_layout.addWidget(self.btn_browse)

        button_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        self.btn_open = QPushButton("Open")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self.accept)
        self.btn_open.setDefault(True)
        button_layout.addWidget(self.btn_open)

        main_layout.addLayout(button_layout)

    def load_projects(self):
        """Load all projects from project manager"""
        # Get all projects and store them
        self.all_projects = self.project_manager.get_all_projects()

        # Apply current filters and display
        self.refresh_display()

    def refresh_display(self):
        """Refresh the display with filtered and sorted projects"""
        # Clear existing cards
        for card in self.project_cards:
            card.deleteLater()
        self.project_cards.clear()

        # Get filtered and sorted projects
        projects = self.get_filtered_sorted_projects()

        if not projects:
            # Show "no projects" message
            if self.all_projects:
                message = "No projects match your search."
            else:
                message = "No projects found.\nCreate a new project to get started."

            label = QLabel(message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #999; font-size: 12pt; padding: 50px;")
            self.grid_layout.addWidget(label, 0, 0, 1, 4)
            return

        # Create cards in 4-column grid
        for idx, project in enumerate(projects):
            row = idx // 4
            col = idx % 4

            card = ProjectCard(project, self.grid_container, dialog=self)
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_double_clicked)

            self.grid_layout.addWidget(card, row, col)
            self.project_cards.append(card)

    def get_filtered_sorted_projects(self):
        """Get projects filtered by search and sorted by selection"""
        projects = self.all_projects.copy()

        # Apply search filter
        if hasattr(self, 'search_box'):
            search_text = self.search_box.text().lower().strip()
            if search_text:
                projects = [p for p in projects if search_text in p['name'].lower()]

        # Apply sorting
        if hasattr(self, 'sort_combo'):
            sort_index = self.sort_combo.currentIndex()
            if sort_index == 0:  # Last Modified (Newest)
                projects.sort(key=lambda x: x['last_modified'], reverse=True)
            elif sort_index == 1:  # Last Modified (Oldest)
                projects.sort(key=lambda x: x['last_modified'], reverse=False)
            elif sort_index == 2:  # Name (A-Z)
                projects.sort(key=lambda x: x['name'].lower())
            elif sort_index == 3:  # Name (Z-A)
                projects.sort(key=lambda x: x['name'].lower(), reverse=True)

        return projects

    def on_search_changed(self):
        """Handle search text change"""
        self.refresh_display()

    def on_sort_changed(self):
        """Handle sort selection change"""
        self.refresh_display()

    def _on_card_clicked(self, project_data):
        """Handle card click"""
        # Deselect all other cards
        for card in self.project_cards:
            if card.project_data == project_data:
                card.setSelected(True)
                self.selected_project = project_data
            else:
                card.setSelected(False)

        # Enable open button
        self.btn_open.setEnabled(True)

    def _on_card_double_clicked(self, project_data):
        """Handle card double-click (open immediately)"""
        self.selected_project = project_data
        self.accept()

    def delete_project(self, project_data):
        """Handle project deletion"""
        filepath = project_data['filepath']
        success = self.project_manager.delete_project(filepath)

        if success:
            # Reload and refresh projects
            self.all_projects = self.project_manager.get_all_projects()
            self.refresh_display()
            self.selected_project = None
            self.btn_open.setEnabled(False)
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete project '{project_data['name']}'"
            )

    def rename_project(self, project_data, new_name):
        """Handle project renaming"""
        old_path = project_data['filepath']
        new_path = self.project_manager.rename_project(old_path, new_name)

        if new_path:
            # Reload and refresh projects
            self.all_projects = self.project_manager.get_all_projects()
            self.refresh_display()
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to rename project. A project with that name may already exist."
            )

    def on_browse_clicked(self):
        """Handle browse button click to open file from another location"""
        from PyQt6.QtWidgets import QFileDialog
        import os

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project File",
            os.path.expanduser("~"),
            "ECis Project Files (*.ecis);;All Files (*)"
        )

        if file_path:
            # Validate that it's an .ecis file
            if not file_path.endswith('.ecis'):
                QMessageBox.critical(
                    self,
                    "Invalid File Type",
                    "Please select a valid .ecis project file.\n\n"
                    "The selected file is not an ECis project file."
                )
                return

            # Validate that the file exists and is readable
            try:
                from pathlib import Path
                filepath = Path(file_path)

                if not filepath.exists():
                    QMessageBox.critical(
                        self,
                        "File Not Found",
                        f"The selected file does not exist:\n{file_path}"
                    )
                    return

                # Try to load it to ensure it's valid
                project_data = self.project_manager.load_project(filepath)
                if project_data is None:
                    QMessageBox.critical(
                        self,
                        "Invalid Project File",
                        "The selected file is not a valid ECis project file.\n\n"
                        "The file may be corrupted or in an incorrect format."
                    )
                    return

                # File is valid, store it and accept the dialog
                self.browsed_file = filepath
                self.accept()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Opening File",
                    f"An error occurred while opening the file:\n\n{str(e)}"
                )

    def get_selected_project_path(self) -> Optional[Path]:
        """Get the filepath of the selected project"""
        # Prioritize browsed file
        if self.browsed_file:
            return self.browsed_file

        if self.selected_project:
            return self.selected_project['filepath']
        return None
