# game.grid
import pygame as py

from game.chunk import CHUNK_SIZE


def four_neighbor_coords(x, y):
    """The 4 orthogonally-adjacent grid coordinates around (x, y)."""
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


class Grid:
    """Draws the faint grid lines over the ground so the tiles are easy to
    see, mostly while building."""

    CELL_SIZE = 32

    CHUNK_LINE_COLOR = (255, 140, 0)
    CHUNK_LINE_ALPHA = 160
    CHUNK_LINE_WIDTH = 2

    def __init__(self, color=(204, 204, 204), alpha=120):
        self.color = color
        self.alpha = alpha
        self.pattern_surface = self._build_pattern_surface()

    def _build_pattern_surface(self):
        """Makes one small tile with just two edges drawn on it, so the
        whole grid can be built by stamping this everywhere instead of
        drawing every line by hand."""
        cell = self.CELL_SIZE
        surface = py.Surface((cell, cell), py.SRCALPHA)
        py.draw.line(surface, (*self.color, self.alpha), (0, 0), (0, cell))
        py.draw.line(surface, (*self.color, self.alpha), (0, 0), (cell, 0))
        return surface

    def draw(self, screen, camera):
        """Tiles the little grid pattern across the whole screen, shifted
        by the camera so it looks like it's actually part of the world
        instead of stuck to the screen."""
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

    def draw_chunk_borders(self, screen, camera):
        """Draws a heavier line along every chunk boundary (every
        CHUNK_SIZE tiles), so it's easy to see where one chunk ends and the
        next begins - mostly useful for eyeballing chunk-crossing belts."""
        width, height = screen.get_size()
        chunk_size_px = self.CELL_SIZE * CHUNK_SIZE

        offset_x = -camera.x % chunk_size_px
        offset_y = -camera.y % chunk_size_px

        overlay = py.Surface((width, height), py.SRCALPHA)
        color = (*self.CHUNK_LINE_COLOR, self.CHUNK_LINE_ALPHA)

        x = offset_x - chunk_size_px
        while x <= width:
            py.draw.line(overlay, color, (x, 0), (x, height), self.CHUNK_LINE_WIDTH)
            x += chunk_size_px

        y = offset_y - chunk_size_px
        while y <= height:
            py.draw.line(overlay, color, (0, y), (width, y), self.CHUNK_LINE_WIDTH)
            y += chunk_size_px

        screen.blit(overlay, (0, 0))