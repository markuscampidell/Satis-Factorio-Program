# systems.conveyors.ghost_belt_renderer
import pygame as py

from core.vector2 import Vector2

class GhostBeltRenderer:
    def __init__(self, sprite_manager, cell_size):
        self.cell_size = cell_size
        self.sprite_manager = sprite_manager
        self.cache = {} # Cache for ghost belt images

        self.color_overlays = {"red": self._make_overlay((255, 0, 0, 120)),
                               "orange": self._make_overlay((255, 165, 0, 120)),
                               "yellow": self._make_overlay((255, 255, 0, 120)),}

    def draw_single(self, screen, camera, grid_pos, incoming: Vector2, outgoing: Vector2, color="normal"):
        # Convert tile → pixel
        tile_x, tile_y = grid_pos
        x = tile_x * self.cell_size
        y = tile_y * self.cell_size

        incoming = Vector2(round(incoming.x), round(incoming.y))
        outgoing = Vector2(round(outgoing.x), round(outgoing.y))

        if incoming == outgoing: key = ("straight", outgoing.x, outgoing.y)
        else: key = ("curve", incoming.x, incoming.y, outgoing.x, outgoing.y)

        if key not in self.cache:
            if key[0] == "straight": base_img = self.sprite_manager.get_straight(outgoing)
            else: base_img = self.sprite_manager.get_curve(incoming, outgoing)

            if base_img is None: return

            scaled = py.transform.scale(base_img, (self.cell_size, self.cell_size))
            ghost = scaled.copy()
            ghost.set_alpha(160)

            self.cache[key] = ghost

        screen.blit(self.cache[key], (x - camera.x, y - camera.y))

        if color in self.color_overlays:
            screen.blit(self.color_overlays[color], (x - camera.x, y - camera.y))

    def draw_dragging(self, screen, camera, segments, color_flags=None):
        for i, seg in enumerate(segments):
            outgoing = seg.direction or Vector2(1, 0)
            incoming = seg.incoming_direction or outgoing
            color = color_flags[i] if color_flags else "normal"

            self.draw_single(screen, camera, seg.grid_pos, incoming, outgoing, color)

    def _make_overlay(self, color):
        surface = py.Surface((self.cell_size, self.cell_size), py.SRCALPHA)
        surface.fill(color)
        return surface