# systems.rendering.build_mode_renderer
import pygame as py

from objects.conveyors.belt_segment import BeltSegment

class BuildModeRenderer:
    def __init__(self, build_system, machine_system, ghost_belt_drawer, belt_system , camera, grid):
        self.build_system = build_system
        self.machine_system = machine_system
        self.ghost_belt_drawer = ghost_belt_drawer
        self.belt_system = belt_system
        self.camera = camera

        self.update_overlay_surfaces(camera.screen_width, camera.screen_height)

    def draw(self, screen):
        self._draw_build_overlay(screen)
        self._draw_delete_overlay(screen)
        self._draw_ghost()
        self._highlight_hovered_delete_target(screen)
        
    def _draw_ghost(self):
        if (self.build_system.build_mode == "building" and self.build_system.selected_machine_class is not None):
            self.machine_system.ghost_machine(self.build_system.selected_machine_class, self.build_system.build_mode, self.machine_system.splitter_rotation_steps)
            self.ghost_belt_drawer.draw_ghost(self.build_system.selected_machine_class, self.belt_system.placing_belt, self.belt_system.selected_belt_type)

    def _highlight_hovered_delete_target(self, screen):
        if self.build_system.build_mode != "deleting" or self.build_system.hovered_delete_target is None: return

        alpha = 100
        color = (255, 0, 0)
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        if isinstance(self.build_system.hovered_delete_target, BeltSegment) and shift_held:
            segments_to_highlight = self.belt_system.get_connected_belt_segments(self.build_system.hovered_delete_target)
        else:
            segments_to_highlight = [self.build_system.hovered_delete_target]

        for obj in segments_to_highlight:
            if hasattr(obj, "rect"):
                rect = obj.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill((*color, alpha))
                screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))
    
    def _draw_build_overlay(self, screen):
        if self.build_system.build_mode == "building":
            screen.blit(self.overlay_build_place, (0, 0))
    
    def _draw_delete_overlay(self, screen):
        if self.build_system.build_mode == "deleting":
            screen.blit(self.overlay_delete, (0, 0))
    
    def update_overlay_surfaces(self, width, height):
        self.overlay_build_place = py.Surface((width, height), py.SRCALPHA)
        self.overlay_build_place.fill((255, 170, 80, 28))

        self.overlay_delete = py.Surface((width, height), py.SRCALPHA)
        self.overlay_delete.fill((255, 80, 80, 35))