import pygame as py

class Machine:
    SIZE = 96
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, pos):
        self.rect = py.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = pos

        self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            self.image.blit(py.transform.scale(original, (self.SIZE, self.SIZE)), (0, 0))