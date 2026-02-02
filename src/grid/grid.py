import pygame as py

class Grid:
    CELL_SIZE = 32

    def __init__(self, screen_width, screen_height, color=(204, 204, 204)):
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.grid_surface = py.Surface((screen_width, screen_height), py.SRCALPHA)
        self.last_camera_pos = None
        self.build_grid_surface()

    def build_grid_surface(self, alpha=120):
        self.grid_surface.fill((0, 0, 0, 0))
        size = self.CELL_SIZE
        w, h = self.screen_width, self.screen_height

        for x in range(0, w, size):
            py.draw.line(self.grid_surface, (*self.color, alpha), (x, 0), (x, h))
        for y in range(0, h, size):
            py.draw.line(self.grid_surface, (*self.color, alpha), (0, y), (w, y))

    def draw(self, screen, camera):
        if self.last_camera_pos != (camera.x, camera.y):
            self.last_camera_pos = (camera.x, camera.y)
            self.build_grid_surface()

        offset_x = -camera.x % self.CELL_SIZE
        offset_y = -camera.y % self.CELL_SIZE
        screen.blit(self.grid_surface, (offset_x - self.CELL_SIZE, offset_y - self.CELL_SIZE))