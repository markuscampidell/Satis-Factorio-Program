import pygame as py

class Grid:
    CELL_SIZE = 32

    def __init__(self, color=(204, 204, 204), alpha=120):
        self.color = color
        self.alpha = alpha
        self.pattern_surface = self._build_pattern_surface()

    def _build_pattern_surface(self):
        cell = self.CELL_SIZE
        surface = py.Surface((cell, cell), py.SRCALPHA)
        py.draw.line(surface, (*self.color, self.alpha), (0, 0), (0, cell))
        py.draw.line(surface, (*self.color, self.alpha), (0, 0), (cell, 0))
        return surface

    def draw(self, screen, camera):
        width, height = screen.get_size()
        cell = self.CELL_SIZE

        offset_x = -camera.x % cell
        offset_y = -camera.y % cell

        tiles_x = (width // cell) + 2
        tiles_y = (height // cell) + 2

        for y in range(tiles_y):
            for x in range(tiles_x):
                screen.blit(self.pattern_surface, (x * cell + offset_x - cell, y * cell + offset_y - cell))
    
    def update_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height