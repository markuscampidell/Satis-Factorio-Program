# systems.conveyors.ghost_belt_drawer

import pygame as py
from objects.conveyors.belt_segment import BeltSegment
from core.vector2 import Vector2


class BeltGhostPreviewController:
    def __init__(
        self,
        world,
        player,
        grid,
        belt_system,
        ghost_renderer,
        camera,
        screen
    ):
        self.world = world
        self.player = player
        self.grid = grid
        self.belt_system = belt_system
        self.ghost_renderer = ghost_renderer
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

        allow_replace_belts, allow_replace_machines = self.belt_system.get_placement_modifiers()

        # Single belt
        if not placing_belt:
            if self.belt_system.is_tile_blocked_for_placement(mouse_tile, allow_replace_belts, allow_replace_machines):
                    color_flag = "red"

            elif self.player.inventory.has_enough_items(self.belt_system.BUILD_COSTS[selected_belt_type]):
                color_flag = "normal"

            else:
                color_flag = "yellow"

            direction = (self.belt_system.belt_placement_direction or Vector2(1, 0)).snapped()

            self.ghost_renderer.draw_single(self.screen, self.camera, mouse_tile, [direction], direction, color_flag)

            return

        # Multiple belt dragging

        tiles = self.belt_system._get_tiles_for_drag(start_tile, mouse_tile,
            horizontal_first=(self.belt_system.belt_first_axis_horizontal))

        segments = self.belt_system._tiles_to_segments(tiles, belt_type=selected_belt_type)

        # Calculate what the entire belt network would look like if these ghost belts were placed.
        affected_segments = (self.belt_system.resolve_preview_connections(segments))

        # Check blocking
        any_blocked = any(
            self.belt_system.is_tile_blocked_for_placement(seg.grid_pos, allow_replace_belts, allow_replace_machines)
            for seg in segments
        )

        if any_blocked:
            color_flags = ["red"] * len(segments)

        elif allow_replace_belts or allow_replace_machines:
            # Replacing belts/machines is all-or-nothing (BeltSystem.place_belt
            # dry-runs the whole thing before touching anything) - so show the
            # whole drag in one color reflecting why it would fail, rather than
            # a per-tile mix that implies a partial placement could happen.
            replaced_segments, replaced_machines, total_cost = self.belt_system.gather_replacements(
                segments, selected_belt_type
            )
            status = self.belt_system.check_placement_affordability(replaced_segments, replaced_machines, total_cost)
            color = {"ok": "normal", "no_space": "orange", "no_funds": "yellow"}[status]
            color_flags = [color] * len(segments)

        else:
            # Fresh placement over empty tiles: show per-tile affordability
            # as the player's inventory would be spent down segment by segment.
            available = {
                item_id: self.player.inventory.get_amount(item_id)
                for item_id in self.belt_system.BUILD_COSTS[selected_belt_type]
            }

            color_flags = []

            for seg in segments:
                can_build = all(
                    available[item_id] >= cost
                    for item_id, cost
                    in self.belt_system.BUILD_COSTS[
                        seg.belt_type
                    ].items()
                )

                if can_build:
                    color_flags.append("normal")

                    for item_id, cost in (
                        self.belt_system.BUILD_COSTS[
                            seg.belt_type
                        ].items()
                    ):
                        available[item_id] -= cost

                else:
                    color_flags.append("yellow")

        # ---------------------------------------------------------
        # Camera visibility
        # ---------------------------------------------------------

        cam_tile_x1, cam_tile_y1 = self.world.snap_to_tile(
            self.camera.x,
            self.camera.y
        )

        cam_tile_x2, cam_tile_y2 = self.world.snap_to_tile(
            self.camera.x + self.camera.screen_width,
            self.camera.y + self.camera.screen_height
        )

        visible_segments = []
        visible_flags = []

        for seg, flag in zip(segments, color_flags):
            x, y = seg.grid_pos

            if (
                cam_tile_x1 <= x <= cam_tile_x2
                and cam_tile_y1 <= y <= cam_tile_y2
            ):
                visible_segments.append(seg)
                visible_flags.append(flag)

        # ---------------------------------------------------------
        # Draw existing belts whose appearance would change
        # ---------------------------------------------------------

        visible_affected = []

        for seg, incoming_directions in affected_segments:
            x, y = seg.grid_pos

            if not (
                cam_tile_x1 <= x <= cam_tile_x2
                and cam_tile_y1 <= y <= cam_tile_y2
            ):
                continue

            # Only draw it if the preview actually changes it.
            if incoming_directions != seg.incoming_directions:
                visible_affected.append(
                    (seg, incoming_directions)
                )

        self.ghost_renderer.draw_affected_segments(
            self.screen,
            self.camera,
            visible_affected
        )

        # ---------------------------------------------------------
        # Draw new ghost belts
        # ---------------------------------------------------------

        self.ghost_renderer.draw_dragging(
            self.screen,
            self.camera,
            visible_segments,
            color_flags=visible_flags
        )

    def draw_delete_ghost(self, segments_to_delete):
        affected_segments = (
            self.belt_system.resolve_delete_preview_connections(
                segments_to_delete
            )
        )

        # Camera visibility
        cam_tile_x1, cam_tile_y1 = self.world.snap_to_tile(
            self.camera.x,
            self.camera.y
        )

        cam_tile_x2, cam_tile_y2 = self.world.snap_to_tile(
            self.camera.x + self.camera.screen_width,
            self.camera.y + self.camera.screen_height
        )

        visible_affected = []

        for seg, incoming_directions in affected_segments:
            x, y = seg.grid_pos

            if (
                cam_tile_x1 <= x <= cam_tile_x2
                and cam_tile_y1 <= y <= cam_tile_y2
            ):
                visible_affected.append(
                    (seg, incoming_directions)
                )

        self.ghost_renderer.draw_affected_segments(
            self.screen,
            self.camera,
            visible_affected
        )