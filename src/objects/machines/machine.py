# objects.machines.machine
import pygame as py

from core.vector2 import Vector2

class Machine:
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, grid_pos, cell_size):
        self.grid_pos = grid_pos
        self.cell_size = cell_size

        # Make rect match tile size
        self.rect = py.Rect(
            grid_pos[0] * cell_size,
            grid_pos[1] * cell_size,
            self.WIDTH * cell_size,
            self.HEIGHT * cell_size
        )

        # Load and scale image to rect
        self.image = None
        if self.SPRITE_PATH:
            self.image = py.image.load(self.SPRITE_PATH).convert_alpha()
            self.image = py.transform.scale(self.image, (self.rect.width, self.rect.height))

    def _compute_occupied_cells(self):
        return [
            (self.grid_pos[0] + dx, self.grid_pos[1] + dy)
            for dx in range(self.WIDTH)
            for dy in range(self.HEIGHT)
        ]

    @property
    def occupied_cells(self):
        if not hasattr(self, '_occupied_cells') or self._occupied_cells is None:
            self._occupied_cells = self._compute_occupied_cells()
        return self._occupied_cells

    def _get_output_tiles(self):
            """(tile_offset, direction) for every tile around the machine's
            entire perimeter - it can push output out any side, not just one
            fixed tile. tile_offset is relative to grid_pos (top-left
            corner); direction is the unit vector pointing outward through
            that tile."""
            tiles = []
    
            for dy in range(self.HEIGHT):
                tiles.append(((self.WIDTH, dy), Vector2(1, 0)))    # right edge
                tiles.append(((-1, dy), Vector2(-1, 0)))           # left edge
    
            for dx in range(self.WIDTH):
                tiles.append(((dx, -1), Vector2(0, -1)))           # top edge
                tiles.append(((dx, self.HEIGHT), Vector2(0, 1)))   # bottom edge
    
            return tiles

    def get_refund_items(self):
        """Items the player should get back if this machine is destroyed,
        as an {item_id: amount} dict. Subclasses add whatever they hold on
        top of the base build cost."""
        return dict(self.BUILD_COST)