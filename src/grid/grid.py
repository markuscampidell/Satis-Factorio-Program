import pygame as py

class Grid:
    def __init__(self, cell_size, screen_width, screen_height, color = ("#CCCCCC")):
        self.cell_size = cell_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.color = color

    def draw(self, screen, camera):
        start_x = -camera.x % self.cell_size
        start_y = -camera.y % self.cell_size

        for x in range(start_x, self.screen_width, self.cell_size):
            py.draw.line(screen, self.color, (x, 0), (x, self.screen_height))
        for y in range(start_y, self.screen_height, self.cell_size):
            py.draw.line(screen, self.color, (0, y), (self.screen_width, y))
