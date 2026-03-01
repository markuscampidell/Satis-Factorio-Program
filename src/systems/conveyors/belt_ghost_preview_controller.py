# systems.conveyors.ghost_belt_drawer
import pygame as py
from objects.conveyors.belt_segment import BeltSegment
from core.vector2 import Vector2

class BeltGhostPreviewController:
    def __init__(self, world, player, grid, belt_system, ghost_renderer, camera, screen):
        self.world = world
        self.player = player
        self.grid = grid
        self.belt_system = belt_system       # Handles belt placement logic
        self.ghost_renderer = ghost_renderer # Handles actual drawing
        self.camera = camera
        self.screen = screen

    def draw_ghost(self, selected_machine_class, placing_belt=False, selected_belt_type="basic"):
        if selected_machine_class is not BeltSegment:
            return

        mx, my = py.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        mouse_tile = self.world.snap_to_tile(world_x, world_y)
        start_tile = (self.belt_system.beltX1, self.belt_system.beltY1)

        # ------------------------
        # SINGLE BELT PREVIEW
        # ------------------------
        if not placing_belt:
            if self.world.is_cell_blocked(mouse_tile) or self.world.is_blocked_by_player(mouse_tile):
                color_flag = "red"
            elif self.player.inventory.has_enough_items(
                self.belt_system.BUILD_COSTS[selected_belt_type]
            ):
                color_flag = "normal"
            else:
                color_flag = "yellow"

            direction = (self.belt_system.belt_placement_direction or Vector2(1, 0)).snapped()
            self.ghost_renderer.draw_single(
                self.screen,
                self.camera,
                mouse_tile,
                direction,
                direction,
                color_flag,
            )
            return

        # ------------------------
        # DRAGGING MULTIPLE TILES
        # ------------------------
        tiles = self.belt_system._get_tiles_for_drag(
            start_tile,
            mouse_tile,
            horizontal_first=self.belt_system.belt_first_axis_horizontal,
        )
        segments = self.belt_system._tiles_to_segments(tiles, belt_type=selected_belt_type)
        self.belt_system.resolve_preview_connections(segments)

        # Check for any blocking (machines, belts, player)
        any_blocked = any(self.world.is_cell_blocked(seg.grid_pos) or self.world.is_blocked_by_player(seg.grid_pos)
                          for seg in segments)

        # Track inventory availability for coloring
        available = {
            item_id: self.player.inventory.get_amount(item_id)
            for item_id in self.belt_system.BUILD_COSTS[selected_belt_type]
        }

        color_flags = []
        for seg in segments:
            if any_blocked:
                color_flags.append("red")
                continue

            can_build = all(
                available[item_id] >= cost
                for item_id, cost in self.belt_system.BUILD_COSTS[seg.belt_type].items()
            )

            if can_build:
                color_flags.append("normal")
                for item_id, cost in self.belt_system.BUILD_COSTS[seg.belt_type].items():
                    available[item_id] -= cost
            else:
                color_flags.append("yellow")

        # ------------------------
        # Tile visibility check for camera
        # ------------------------
        cam_tile_x1, cam_tile_y1 = self.world.snap_to_tile(self.camera.x, self.camera.y)
        cam_tile_x2, cam_tile_y2 = self.world.snap_to_tile(
            self.camera.x + self.camera.screen_width,
            self.camera.y + self.camera.screen_height
        )

        visible_segments = []
        visible_flags = []
        for seg, flag in zip(segments, color_flags):
            x, y = seg.grid_pos
            if cam_tile_x1 <= x <= cam_tile_x2 and cam_tile_y1 <= y <= cam_tile_y2:
                visible_segments.append(seg)
                visible_flags.append(flag)

        # Draw the ghost belts
        self.ghost_renderer.draw_dragging(
            self.screen,
            self.camera,
            visible_segments,
            color_flags=visible_flags
        )