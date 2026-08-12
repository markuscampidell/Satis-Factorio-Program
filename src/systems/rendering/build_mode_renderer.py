# systems.rendering.build_mode_renderer
import pygame as py

from objects.conveyors.belt_segment import BeltSegment

class BuildModeRenderer:
    def __init__(self, build_system, machine_system, ghost_machine_renderer, ghost_belt_drawer, belt_system, camera, grid):
        self.build_system = build_system
        self.machine_system = machine_system
        self.ghost_machine_renderer = ghost_machine_renderer
        self.ghost_belt_drawer = ghost_belt_drawer
        self.belt_system = belt_system
        self.camera = camera
        self.grid = grid

        self.delete_overlay_tile = self._make_tile_overlay((255, 0, 0, 100))
        self.delete_blocked_overlay_tile = self._make_tile_overlay((255, 165, 0, 100))
        self.update_overlay_surfaces(camera.screen_width, camera.screen_height)

    def _make_tile_overlay(self, color):
        surf = py.Surface((self.grid.CELL_SIZE, self.grid.CELL_SIZE), py.SRCALPHA)
        surf.fill(color)
        return surf
    
    def draw(self, screen):
        self._draw_build_overlay(screen)
        self._draw_delete_overlay(screen)
        self._draw_ghost()
        self._draw_delete_ghost()
        self._highlight_hovered_delete_target(screen)
        
    def _draw_ghost(self):
        if (self.build_system.build_mode == "building" and self.build_system.selected_machine_class is not None):
            self.ghost_machine_renderer.draw(self.build_system.selected_machine_class, self.build_system.build_mode, self.machine_system.splitter_rotation_steps)
            self.ghost_belt_drawer.draw_ghost(self.build_system.selected_machine_class, self.belt_system.placing_belt, self.belt_system.selected_belt_type)

    def _highlight_hovered_delete_target(self, screen):
        if self.build_system.build_mode != "deleting" or self.build_system.hovered_delete_target is None:
            return

        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target = self.build_system.hovered_delete_target

        if isinstance(target, BeltSegment) and shift_held:
            segments_to_highlight = self.belt_system.get_connected_belt_segments(target)
        else:
            segments_to_highlight = [target]

        # Orange = targeted, but there isn't enough inventory space to
        # receive the refund, so the click won't actually delete it.
        if isinstance(target, BeltSegment):
            can_delete = self.belt_system.can_afford_belt_deletion(segments_to_highlight)
        else:
            can_delete = self.machine_system.can_afford_deletion(target)

        overlay_tile = self.delete_overlay_tile if can_delete else self.delete_blocked_overlay_tile
        overlay_color = (255, 0, 0, 100) if can_delete else (255, 165, 0, 100)

        for obj in segments_to_highlight:
            # Tile-based highlighting
            if hasattr(obj, "occupied_cells"):
                for grid_x, grid_y in obj.occupied_cells:
                    pixel_x = grid_x * self.grid.CELL_SIZE
                    pixel_y = grid_y * self.grid.CELL_SIZE
                    screen.blit(overlay_tile, (pixel_x - self.camera.x, pixel_y - self.camera.y))
            # Fallback for older objects that still have rect
            elif hasattr(obj, "rect") and obj.rect:
                rect = obj.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill(overlay_color)
                screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))
    
    def _draw_build_overlay(self, screen):
        if self.build_system.build_mode == "building":
            screen.blit(self.overlay_build_place, (0, 0))
    
    def _draw_delete_overlay(self, screen):
        if self.build_system.build_mode == "deleting":
            screen.blit(self.overlay_delete, (0, 0))

    def _draw_delete_ghost(self):
        if (
            self.build_system.build_mode != "deleting"
            or self.build_system.hovered_delete_target is None
        ):
            return

        target = self.build_system.hovered_delete_target

        if not isinstance(target, BeltSegment):
            return

        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        if shift_held:
            segments_to_delete = (
                self.belt_system.get_connected_belt_segments(target)
            )
        else:
            segments_to_delete = [target]

        self.ghost_belt_drawer.draw_delete_ghost(
            segments_to_delete
        )
    
    def update_overlay_surfaces(self, width, height):
        self.overlay_build_place = py.Surface((width, height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))

        self.overlay_delete = py.Surface((width, height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))