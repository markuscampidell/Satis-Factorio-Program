import pygame as py
from core.vector2 import Vector2
from game.grid import Grid
from systems.conveyors.beltspritemanager import BeltSpriteManager


class GhostBeltRenderer:
    def __init__(self, sprite_manager: BeltSpriteManager):
        self.sprite_manager = sprite_manager
        self.cache = {} # Cache for ghost belt images

        self.color_overlays = {"red": self._make_overlay((255, 0, 0, 120)),
                               "orange": self._make_overlay((255, 165, 0, 120)),
                               "yellow": self._make_overlay((255, 255, 0, 120)),}

    def draw_single(self, screen, camera, x, y, incoming: Vector2, outgoing: Vector2, color="normal"):
        cell = Grid.CELL_SIZE
        incoming = Vector2(round(incoming.x), round(incoming.y))
        outgoing = Vector2(round(outgoing.x), round(outgoing.y))

        if incoming == outgoing: key = ("straight", outgoing.x, outgoing.y)
        else: key = ("curve", incoming.x, incoming.y, outgoing.x, outgoing.y)

        if key not in self.cache:
            if key[0] == "straight": base_img = self.sprite_manager.get_straight(outgoing)
            else: base_img = self.sprite_manager.get_curve(incoming, outgoing)

            if base_img is None: return

            scaled = py.transform.scale(base_img, (cell, cell))

            ghost = scaled.copy()
            ghost.set_alpha(160)

            self.cache[key] = ghost

        screen.blit(self.cache[key], (x - camera.x, y - camera.y))

        if color in self.color_overlays:
            screen.blit(self.color_overlays[color], (x - camera.x, y - camera.y))

    def draw_dragging(self, screen, camera, segments, color_flags=None):
        cell = Grid.CELL_SIZE

        for i, seg in enumerate(segments):
            outgoing = (seg.direction if seg.direction is not None else Vector2(1, 0))

            if i == 0: incoming = outgoing  # first segment is always straight
            else:
                prev_seg = segments[i - 1]
                incoming = Vector2((seg.rect.x - prev_seg.rect.x) // cell, (seg.rect.y - prev_seg.rect.y) // cell)

            color = (color_flags[i] if color_flags else "normal")

            self.draw_single(screen, camera, seg.rect.x, seg.rect.y, incoming, outgoing, color)

    def _make_overlay(self, color):
        cell = Grid.CELL_SIZE
        surface = py.Surface((cell, cell), py.SRCALPHA)
        surface.fill(color)
        return surface