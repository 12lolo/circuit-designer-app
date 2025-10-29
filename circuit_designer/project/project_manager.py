import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import QRectF, Qt, QBuffer, QIODevice
from PyQt6.QtGui import QImage, QPainter
import base64


class ProjectManager:
    """Manages project saving, loading, and thumbnail generation"""

    def __init__(self):
        # Default project directory
        home = Path.home()
        self.default_project_dir = home / "PycharmProjects" / "circuit-designer-app" / "projects"
        self._ensure_project_dir()

    def _ensure_project_dir(self):
        """Create the default project directory if it doesn't exist"""
        self.default_project_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail(self, scene: QGraphicsScene, size: int = 200, grid_rect=None) -> str:
        """
        Generate a base64-encoded thumbnail from the graphics scene

        Args:
            scene: QGraphicsScene to render
            size: Thumbnail size (square)
            grid_rect: Optional tuple (x, y, width, height) of the grid to render

        Returns:
            Base64-encoded PNG string
        """
        # Use the provided grid rect, otherwise try to get items bounding rect
        if grid_rect:
            # Grid rect provided (x, y, width, height)
            render_rect = QRectF(grid_rect[0], grid_rect[1], grid_rect[2], grid_rect[3])
        else:
            # Fallback to items bounding rect
            render_rect = scene.itemsBoundingRect()

            # If empty, use scene rect
            if render_rect.isEmpty() or (render_rect.width() <= 0 or render_rect.height() <= 0):
                render_rect = scene.sceneRect()

        # Create image with white background
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)

        # Create painter
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Let Qt handle the scaling automatically
        # Render the source rect (render_rect) to fill the entire target image (size x size)
        target_rect = QRectF(0, 0, size, size)
        scene.render(painter, target_rect, render_rect)
        painter.end()

        # Convert to base64 using QBuffer
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()

        img_bytes = buffer.data().data()  # Get bytes from QByteArray
        base64_str = base64.b64encode(img_bytes).decode('utf-8')

        return base64_str

    def save_project(self, project_data: dict, filename: str, scene: QGraphicsScene, grid_rect=None) -> bool:
        """
        Save project to default directory with embedded thumbnail

        Args:
            project_data: Project data dictionary (components, wires, etc.)
            filename: Filename (without path, e.g., "myproject.ecis")
            scene: Scene to generate thumbnail from
            grid_rect: Optional tuple (x, y, width, height) of grid area to render

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure .ecis extension
            if not filename.endswith('.ecis'):
                filename += '.ecis'

            # Full path
            filepath = self.default_project_dir / filename

            # Generate thumbnail
            thumbnail = self.generate_thumbnail(scene, grid_rect=grid_rect)

            # Add metadata
            project_data['metadata'] = {
                'thumbnail': thumbnail,
                'saved_at': datetime.now().isoformat(),
                'version': project_data.get('version', '1.0')
            }

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    def save_project_copy(self, project_data: dict, filepath: str, scene: QGraphicsScene, grid_rect=None) -> bool:
        """
        Save a copy of the project to any location (for sharing)

        Args:
            project_data: Project data dictionary
            filepath: Full file path
            scene: Scene to generate thumbnail from
            grid_rect: Optional tuple (x, y, width, height) of grid area to render

        Returns:
            True if saved successfully
        """
        try:
            # Ensure .ecis extension
            if not filepath.endswith('.ecis'):
                filepath += '.ecis'

            # Generate thumbnail
            thumbnail = self.generate_thumbnail(scene, grid_rect=grid_rect)

            # Add metadata
            project_data['metadata'] = {
                'thumbnail': thumbnail,
                'saved_at': datetime.now().isoformat(),
                'version': project_data.get('version', '1.0')
            }

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving project copy: {e}")
            return False

    def load_project(self, filepath: Path) -> Optional[dict]:
        """
        Load project from file

        Args:
            filepath: Path to .ecis file

        Returns:
            Project data dictionary or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            return project_data

        except Exception as e:
            print(f"Error loading project: {e}")
            return None

    def get_all_projects(self) -> List[Dict[str, any]]:
        """
        Get list of all projects in default directory with metadata

        Returns:
            List of dicts with keys: name, filepath, thumbnail, last_modified
        """
        projects = []

        try:
            # Find all .ecis files
            for filepath in self.default_project_dir.glob("*.ecis"):
                try:
                    # Get file stats
                    stat = filepath.stat()
                    last_modified = datetime.fromtimestamp(stat.st_mtime)

                    # Try to load thumbnail from file
                    thumbnail = None
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'metadata' in data and 'thumbnail' in data['metadata']:
                                thumbnail = data['metadata']['thumbnail']
                    except:
                        pass

                    projects.append({
                        'name': filepath.stem,  # Filename without extension
                        'filepath': filepath,
                        'thumbnail': thumbnail,
                        'last_modified': last_modified
                    })

                except Exception as e:
                    print(f"Error reading project {filepath}: {e}")
                    continue

            # Sort by last modified (newest first)
            projects.sort(key=lambda x: x['last_modified'], reverse=True)

        except Exception as e:
            print(f"Error scanning project directory: {e}")

        return projects

    def delete_project(self, filepath: Path) -> bool:
        """Delete a project file"""
        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False

    def rename_project(self, old_path: Path, new_name: str) -> Optional[Path]:
        """
        Rename a project file

        Returns:
            New filepath if successful, None otherwise
        """
        try:
            # Ensure .ecis extension
            if not new_name.endswith('.ecis'):
                new_name += '.ecis'

            new_path = old_path.parent / new_name

            # Check if new name already exists
            if new_path.exists():
                print(f"Project {new_name} already exists")
                return None

            old_path.rename(new_path)
            return new_path

        except Exception as e:
            print(f"Error renaming project: {e}")
            return None
