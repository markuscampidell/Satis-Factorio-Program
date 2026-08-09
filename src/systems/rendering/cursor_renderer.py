# systems.rendering.cursor_renderer
import pygame as py

class CursorRenderer:
    def __init__(self, build_system):
        self.build_system = build_system
        self.cursor_radius = 12
        self.cursor_surfaces = {
            'building': self._make_cursor_surface((255, 200, 50, 150)),
            'deleting': self._make_cursor_surface((255, 100, 150, 120)),
            'normal': self._make_cursor_surface((255, 255, 255, 100)),
        }

    def _make_cursor_surface(self, color):
        surface = py.Surface((self.cursor_radius * 2, self.cursor_radius * 2), py.SRCALPHA)
        py.draw.circle(surface, color, (self.cursor_radius, self.cursor_radius), self.cursor_radius)
        py.draw.circle(surface, (0, 0, 0, 200), (self.cursor_radius, self.cursor_radius), self.cursor_radius, width=2)
        return surface

    def draw(self, screen):
        mx, my = py.mouse.get_pos()
        mode = self.build_system.build_mode
        if mode == "building":
            cursor_surface = self.cursor_surfaces['building']
        elif mode == "deleting":
            cursor_surface = self.cursor_surfaces['deleting']
        else:
            cursor_surface = self.cursor_surfaces['normal']

        screen.blit(cursor_surface, (mx - self.cursor_radius, my - self.cursor_radius))