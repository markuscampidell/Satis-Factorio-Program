# systems.rendering.hover_highlight_renderer
import pygame as py


class HoverHighlightRenderer:
    """Draws a translucent white overlay over whatever machine or belt
    MachineInteractionSystem.hovered_object currently points at - a plain
    "you can click this" affordance, independent of build/delete mode
    (those have their own ghost/highlight overlays in BuildModeRenderer)."""

    def __init__(self, machine_interaction_system, camera, grid):
        self.machine_interaction_system = machine_interaction_system
        self.camera = camera
        self.grid = grid

        self.overlay_tile = py.Surface((grid.CELL_SIZE, grid.CELL_SIZE), py.SRCALPHA)
        self.overlay_tile.fill((255, 255, 255, 90))

    def draw(self, screen):
        obj = self.machine_interaction_system.hovered_object
        if obj is None:
            return

        if hasattr(obj, "occupied_cells"):
            for grid_x, grid_y in obj.occupied_cells:
                pixel_x = grid_x * self.grid.CELL_SIZE - self.camera.x
                pixel_y = grid_y * self.grid.CELL_SIZE - self.camera.y
                screen.blit(self.overlay_tile, (pixel_x, pixel_y))
        elif hasattr(obj, "rect") and obj.rect:
            rect = obj.rect
            overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
            overlay.fill((255, 255, 255, 90))
            screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))
