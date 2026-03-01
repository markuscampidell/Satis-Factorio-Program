# systems.rendering.cursor_renderer
import pygame as py

class CursorRenderer:
    def __init__(self, build_system):
        self.build_system = build_system

    def draw(self, screen):
        mx, my = py.mouse.get_pos()
        cursor_radius = 12
        cursor_surface = py.Surface((cursor_radius * 2, cursor_radius * 2), py.SRCALPHA)

        if self.build_system.build_mode == "building": color = (255, 200, 50, 150)
        elif self.build_system.build_mode == "deleting": color = (255, 100, 150, 120)
        else: color = (255, 255, 255, 100)

        py.draw.circle(cursor_surface, color, (cursor_radius, cursor_radius), cursor_radius)
        py.draw.circle(cursor_surface, (0, 0, 0, 200), (cursor_radius, cursor_radius), cursor_radius, width=2)

        screen.blit(cursor_surface, (mx - cursor_radius, my - cursor_radius))