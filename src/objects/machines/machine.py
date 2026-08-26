# objects.machines.machine
import pygame as py

from core.vector2 import Vector2

class Machine:
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = None
    BUILD_COST = {}
    SAVE_TYPE = None  # savable subclasses override with a unique save-file type tag

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

        # WIDTH/HEIGHT/grid_pos never change after construction, so these
        # only ever need computing once rather than on every access.
        self.occupied_cells = self._compute_occupied_cells()
        self._output_tiles = self._compute_output_tiles()

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

    def _compute_output_tiles(self):
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

    def _get_output_tiles(self):
        return self._output_tiles

    def get_refund_items(self):
        """Items the player should get back if this machine is destroyed,
        as an {item_id: amount} dict. Subclasses add whatever they hold on
        top of the base build cost."""
        return dict(self.BUILD_COST)

    def try_receive_item(self, item, source_grid_pos, direction=None, source_speed=None):
        """Try to accept `item` being pushed in from source_grid_pos,
        arriving from `direction` (only meaningful to machines that care
        which side it came from, like Splitter) at `source_speed` tiles/sec
        if known. Returns True if accepted. Single entry point used by
        belts, splitters, and other machines feeding this one, so they all
        get the same acceptance rules with no per-caller special-casing.
        The base implementation always rejects; subclasses that can
        actually hold items (ProducingMachine, Splitter, Storage) override
        this."""
        return False

    def draw(self, screen, camera):
        if not self.image:
            return
        pixel_x = self.grid_pos[0] * self.cell_size - camera.x
        pixel_y = self.grid_pos[1] * self.cell_size - camera.y
        screen.blit(self.image, (pixel_x, pixel_y))

    def to_dict(self):
        """Serialize this machine to a plain JSON-safe dict for save_system.
        Subclasses override to add their own fields, always starting with
        `data = super().to_dict()`."""
        return {"type": self.SAVE_TYPE, "grid_pos": list(self.grid_pos)}

    @classmethod
    def from_dict(cls, data):
        """Construct this machine from a dict produced by to_dict(). Base
        implementation only handles grid_pos; subclasses override to
        restore their own state, since their constructors need different
        arguments and their runtime state differs."""
        return cls(tuple(data["grid_pos"]))