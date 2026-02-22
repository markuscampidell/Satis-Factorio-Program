import pygame as py

from game.grid import Grid

class Machine:
    WIDTH = 1   # in grid cells
    HEIGHT = 1  # in grid cells
    
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, pos):
        self.rect = py.Rect(0, 0, self.pixel_width, self.pixel_height)
        self.rect.center = pos

        self.image = py.Surface((self.pixel_width, self.pixel_height), py.SRCALPHA)

        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            scaled = py.transform.scale(original, (self.pixel_width, self.pixel_height))
            self.image.blit(scaled, (0, 0))
    
    @property
    def pixel_width(self):
        return self.WIDTH * Grid.CELL_SIZE

    @property
    def pixel_height(self):
        return self.HEIGHT * Grid.CELL_SIZE