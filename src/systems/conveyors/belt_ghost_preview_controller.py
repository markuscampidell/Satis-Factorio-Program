# systems.conveyors.ghost_belt_drawer
import pygame as py

from objects.conveyors.belt_segment import BeltSegment
from core.vector2 import Vector2

class BeltGhostPreviewController:
    def __init__(self, world, player, grid, belt_system, ghost_renderer, camera, screen):
        self.world = world
        self.player = player
        self.grid = grid
        self.belt_system = belt_system       # handles placement logic
        self.ghost_renderer = ghost_renderer # handles drawing
        self.camera = camera
        self.screen = screen

    def draw_ghost(self, selected_machine_class, placing_belt=False, selected_belt_type="basic"):
        if selected_machine_class is not BeltSegment: return

        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        if not placing_belt:
            # Single-belt preview
            snapped_x, snapped_y = self.belt_system._snap_to_grid(world_x, world_y)
            temp_rect = py.Rect(snapped_x, snapped_y, self.grid.CELL_SIZE, self.grid.CELL_SIZE)

            if temp_rect.colliderect(camera_rect):
                if self.world.is_rect_blocked(temp_rect): color_flag = "red"
                elif self.player.inventory.has_enough_items(self.belt_system.BUILD_COSTS[selected_belt_type]): color_flag = "normal"
                else: color_flag = "yellow"

                direction = (self.belt_system.belt_placement_direction or Vector2(1, 0)).snapped()
                self.ghost_renderer.draw_single(self.screen, self.camera, snapped_x, snapped_y, direction, direction, color_flag)
            return

        # Dragging multiple belts
        rects = self.belt_system._get_snapped_rects_for_drag(self.belt_system.beltX1, self.belt_system.beltY1, world_x, world_y, horizontal_first=self.belt_system.belt_first_axis_horizontal)
        segments = self.belt_system._rects_to_segments(rects, belt_type=selected_belt_type)
        self.belt_system.resolve_preview_connections(segments)

        any_blocked = any(self.world.is_rect_blocked(rect) for rect in rects)
        available = {item_id: self.player.inventory.get_amount(item_id) for item_id in self.belt_system.BUILD_COSTS[selected_belt_type]}

        color_flags = []
        for seg in segments:
            if any_blocked:
                color_flags.append("red")
                continue
            can_build = all(available[item_id] >= cost for item_id, cost in self.belt_system.BUILD_COSTS[seg.belt_type].items())
            if can_build:
                color_flags.append("normal")
                for item_id, cost in self.belt_system.BUILD_COSTS[seg.belt_type].items():
                    available[item_id] -= cost
            else:
                color_flags.append("yellow")

        visible_segments = []
        visible_flags = []

        for seg, flag in zip(segments, color_flags):
            if seg.rect.colliderect(camera_rect):
                visible_segments.append(seg)
                visible_flags.append(flag)

        self.ghost_renderer.draw_dragging(self.screen, self.camera, visible_segments, color_flags=visible_flags)