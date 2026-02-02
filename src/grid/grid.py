import pygame as py

class Grid:
    CELL_SIZE = 32

    def __init__(self, screen_width, screen_height, color=(204, 204, 204)):
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.build_lines()

    def build_lines(self, alpha=120):
        max_len = max(self.screen_width, self.screen_height)

        self.vline = py.Surface((1, max_len), py.SRCALPHA)
        self.vline.fill((*self.color, alpha))

        self.hline = py.transform.rotate(self.vline, 90)

    def draw(self, screen, camera):
        size = self.CELL_SIZE
        cam_x = camera.x
        cam_y = camera.y

        w, h = screen.get_size()

        start_x = int(-cam_x % size)
        start_y = int(-cam_y % size)

        for x in range(start_x, w, size):
            screen.blit(self.vline, (x, 0))

        for y in range(start_y, h, size):
            screen.blit(self.hline, (0, y))
