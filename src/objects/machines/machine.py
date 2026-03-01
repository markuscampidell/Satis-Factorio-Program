# objects.machines.machine
import pygame as py

from game.grid import Grid

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

    @property
    def occupied_cells(self):
        return [
            (self.grid_pos[0] + dx, self.grid_pos[1] + dy)
            for dx in range(self.WIDTH)
            for dy in range(self.HEIGHT)
        ]