"""
Optimized spatial grid for fast component placement and overlap detection.
Uses a hash map for O(1) lookups instead of O(n) iteration.
"""

from typing import Set, Tuple, Optional
from components import ComponentItem


class SpatialGrid:
    """
    Spatial hash map for tracking occupied grid cells.
    Provides fast O(1) overlap detection for component placement.
    """

    def __init__(self):
        self.occupied_cells: dict[Tuple[int, int], ComponentItem] = {}

    def clear(self):
        """Clear all tracked cells."""
        self.occupied_cells.clear()

    def add_component(self, component: ComponentItem):
        """
        Add a component and mark its occupied cells.

        Args:
            component: Component to add
        """
        if not hasattr(component, 'get_occupied_grid_cells'):
            return

        cells = component.get_occupied_grid_cells()
        for cell in cells:
            self.occupied_cells[cell] = component

    def remove_component(self, component: ComponentItem):
        """
        Remove a component and free its occupied cells.

        Args:
            component: Component to remove
        """
        if not hasattr(component, 'get_occupied_grid_cells'):
            return

        cells = component.get_occupied_grid_cells()
        for cell in cells:
            if self.occupied_cells.get(cell) == component:
                del self.occupied_cells[cell]

    def update_component(self, component: ComponentItem):
        """
        Update a component's position in the grid.
        More efficient than remove + add for moves.

        Args:
            component: Component to update
        """
        # For now, just remove and re-add
        # Could optimize further by computing delta
        self.remove_component(component)
        self.add_component(component)

    def check_overlap(self, cells: Set[Tuple[int, int]], exclude_component: Optional[ComponentItem] = None) -> bool:
        """
        Check if any of the given cells are occupied.

        Args:
            cells: Set of (gx, gy) grid cells to check
            exclude_component: Optional component to exclude from check (for moves)

        Returns:
            True if any cell is occupied (by a different component)
        """
        for cell in cells:
            occupant = self.occupied_cells.get(cell)
            if occupant is not None and occupant != exclude_component:
                return True
        return False

    def find_free_position(
        self,
        start_gx: int,
        start_gy: int,
        width_cells: int,
        height_cells: int,
        min_gx: int,
        max_gx: int,
        min_gy: int,
        max_gy: int,
        max_radius: int = 40
    ) -> Optional[Tuple[int, int]]:
        """
        Find the nearest free grid position for a component using spiral search.

        Args:
            start_gx, start_gy: Starting anchor position
            width_cells, height_cells: Component size in cells
            min_gx, max_gx, min_gy, max_gy: Grid boundaries
            max_radius: Maximum search radius

        Returns:
            (gx, gy) tuple of free position, or None if not found
        """
        # Helper to check if a position is valid
        def is_position_free(ax: int, ay: int) -> bool:
            # Generate footprint at this anchor
            cells = set()
            if width_cells >= height_cells:  # Horizontal
                for dx in range(width_cells):
                    cells.add((ax + dx, ay))
            else:  # Vertical
                for dy in range(height_cells):
                    cells.add((ax, ay + dy))

            # Check boundaries
            for cx, cy in cells:
                if cx < min_gx or cx > max_gx or cy < min_gy or cy > max_gy:
                    return False

            # Check occupation
            return not self.check_overlap(cells)

        # Test start position first
        if is_position_free(start_gx, start_gy):
            return (start_gx, start_gy)

        # Spiral search outward
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check perimeter (not interior)
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    ax = start_gx + dx
                    ay = start_gy + dy

                    if is_position_free(ax, ay):
                        return (ax, ay)

        return None

    def rebuild_from_scene(self, scene):
        """
        Rebuild spatial grid from all components in scene.

        Args:
            scene: QGraphicsScene containing components
        """
        self.clear()

        for item in scene.items():
            if hasattr(item, 'component_type'):
                self.add_component(item)
