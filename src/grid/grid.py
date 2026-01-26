import pygame as py

class Grid:
    CELL_SIZE = 32
    def __init__(self, screen_width, screen_height, color = ("#CCCCCC")):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.color = color

    def draw(self, screen, camera):
        start_x = -camera.x % self.CELL_SIZE
        start_y = -camera.y % self.CELL_SIZE

        for x in range(start_x, self.screen_width, self.CELL_SIZE):
            py.draw.line(screen, self.color, (x, 0), (x, self.screen_height))
        for y in range(start_y, self.screen_height, self.CELL_SIZE):
            py.draw.line(screen, self.color, (0, y), (self.screen_width, y))
