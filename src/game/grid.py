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
    CHUNK_LINE_WIDTH = 2

    def __init__(self, color=(204, 204, 204)):
        self.color = color

    def _draw_line_grid(self, surface, camera, spacing, color, line_width):
        """Draws a repeating grid of lines `spacing` pixels apart, shifted
        by the camera - the actual lines, drawn directly onto `surface`
        (no intermediate overlay) at a flat, opaque color. A translucent
        version needs a full-screen per-pixel-alpha surface blitted every
        frame to blend against whatever's underneath, which turned out to
        be by far the most expensive part of drawing the grid at all - an
        opaque line is a small fraction of the cost for a difference
        that's barely visible on a thin line anyway."""
        width, height = surface.get_size()

        offset_x = -camera.x % spacing
        x = offset_x - spacing
        while x <= width:
            py.draw.line(surface, color, (x, 0), (x, height), line_width)
            x += spacing

        offset_y = -camera.y % spacing
        y = offset_y - spacing
        while y <= height:
            py.draw.line(surface, color, (0, y), (width, y), line_width)
            y += spacing

    def draw(self, screen, camera):
        """Draws the faint per-tile grid lines over the ground, shifted by
        the camera so it looks like it's actually part of the world
        instead of stuck to the screen."""
        self._draw_line_grid(screen, camera, self.CELL_SIZE, self.color, 1)

    def update_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height

    def draw_chunk_borders(self, screen, camera):
        """Draws a heavier line along every chunk boundary (every
        CHUNK_SIZE tiles), so it's easy to see where one chunk ends and the
        next begins - mostly useful for eyeballing chunk-crossing belts."""
        self._draw_line_grid(screen, camera, self.CELL_SIZE * CHUNK_SIZE, self.CHUNK_LINE_COLOR, self.CHUNK_LINE_WIDTH)