# systems.conveyors.ghost_belt_drawer

import pygame as py
from objects.conveyors.belt_segment import BeltSegment
from core.vector2 import Vector2


class BeltGhostPreviewController:
    """Draws a see-through preview of belts before you actually place or
    delete them, tinted a color that shows if you can afford it."""

    def __init__(self, world, player, grid, belt_system, ghost_renderer, camera, screen):
        self.world = world
        self.player = player
        self.grid = grid
        self.belt_system = belt_system
        self.ghost_renderer = ghost_renderer
        self.camera = camera
        self.screen = screen

    def _camera_tile_bounds(self):
        """(x1, y1, x2, y2) grid-tile bounds of what's currently on screen."""
        x1, y1 = self.world.snap_to_tile(self.camera.x, self.camera.y)
        x2, y2 = self.world.snap_to_tile(
            self.camera.x + self.camera.screen_width,
            self.camera.y + self.camera.screen_height
        )
        return x1, y1, x2, y2

    def _draw_affected(self, affected_segments, only_if_changed=True):
        """Filter existing belts whose sprite would change by camera
        visibility, then draw them - shared by the single-tile, dragging,
        and delete preview paths (and by GhostMachineRenderer for the
        splitter preview)."""
        cam_tile_x1, cam_tile_y1, cam_tile_x2, cam_tile_y2 = self._camera_tile_bounds()

        visible_affected = []

        for seg, incoming_directions in affected_segments:
            x, y = seg.grid_pos

            if not (cam_tile_x1 <= x <= cam_tile_x2 and cam_tile_y1 <= y <= cam_tile_y2):
                continue

            if only_if_changed and incoming_directions == seg.incoming_directions:
                continue

            visible_affected.append((seg, incoming_directions))

        self.ghost_renderer.draw_affected_segments(self.screen, self.camera, visible_affected)

    def _drag_affordability_flags(self, segments):
        """Per-tile "normal" (can afford) / "yellow" (can't) coloring for
        an unblocked drag - walks the segments in order against a running
        scratch copy of the player's inventory, refunding whatever each
        tile would actually replace before charging that tile's own build
        cost, so a long line shows normal exactly as far as you can
        currently afford and yellow from there on. A multi-tile machine
        that the drag crosses more than one cell of is only ever refunded
        once, matching what actually placing it would do."""
        scratch = self.player.inventory.clone()
        seen_machine_ids = set()
        color_flags = []

        for seg in segments:
            replaced_segments, replaced_machines = self.world.gather_occupants([seg.grid_pos])
            replaced_machines = [m for m in replaced_machines if id(m) not in seen_machine_ids]
            seen_machine_ids.update(id(m) for m in replaced_machines)

            cost = self.belt_system.BUILD_COSTS[seg.belt_type]
            refund_ok = self.belt_system.apply_refunds(scratch, replaced_segments, replaced_machines)

            if refund_ok and scratch.try_remove_items(cost):
                color_flags.append("normal")
            else:
                color_flags.append("yellow")

        return color_flags

    def draw_ghost(self, selected_machine_class, placing_belt=False, selected_belt_type="basic"):
        """Draws the belt placement preview: a single tile if you've only
        just started, or the whole dragged-out line (colored by whether
        you can afford it) once you're dragging."""
        if selected_machine_class is not BeltSegment:
            return

        mx, my = py.mouse.get_pos()

        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        mouse_tile = self.world.snap_to_tile(world_x, world_y)
        start_tile = (self.belt_system.beltX1, self.belt_system.beltY1)

        allow_replace = self.belt_system.get_placement_modifiers()

        # Single belt - not dragging yet, just hovering where a click would
        # start (and, if released without moving, immediately finish) a
        # one-tile drag, so it uses the exact same blocked/auto-replace
        # check as an actual drag would for that one tile.
        if not placing_belt:
            direction = (self.belt_system.belt_placement_direction or Vector2(1, 0)).snapped()
            ghost_seg = BeltSegment(mouse_tile, direction, [], belt_type=selected_belt_type)

            if self.belt_system.is_drag_tile_blocked(ghost_seg, None, mouse_tile, True, allow_replace):
                color_flag = "red"
            else:
                replaced_segments, replaced_machines, total_cost = self.belt_system.gather_replacements(
                    [ghost_seg], selected_belt_type
                )
                status = self.belt_system.check_placement_affordability(replaced_segments, replaced_machines, total_cost)
                color_flag = {"ok": "normal", "no_space": "orange", "no_funds": "yellow"}[status]

            affected_segments = self.belt_system.resolve_preview_connections([ghost_seg])
            self._draw_affected(affected_segments)

            self.ghost_renderer.draw_single(self.screen, self.camera, mouse_tile, ghost_seg.incoming_directions, direction, color_flag)

            return

        # Multiple belt dragging

        tiles = self.belt_system.get_drag_tiles(start_tile, mouse_tile)

        segments = self.belt_system._tiles_to_segments(tiles, belt_type=selected_belt_type)

        # Calculate what the entire belt network would look like if these ghost belts were placed.
        affected_segments = (self.belt_system.resolve_preview_connections(segments))

        # Check blocking - a tile can be fine to place on without Shift
        # held, either because it's empty or because it qualifies for the
        # auto-replace rules (the drag's own start tile replacing an
        # existing belt there, or any tile that's already an exact match).
        others_ok = self.belt_system._others_free_or_direction_matching(segments, start_tile)
        new_incomings = self.belt_system._new_incoming_directions(segments)
        any_blocked = any(
            self.belt_system.is_drag_tile_blocked(seg, new_in, start_tile, others_ok, allow_replace)
            for seg, new_in in zip(segments, new_incomings)
        )

        if any_blocked:
            color_flags = ["red"] * len(segments)

        else:
            # Nothing's blocked, so color each tile on its own running
            # affordability - normal as far as you can actually afford,
            # yellow from there on - rather than one lump verdict for the
            # whole line (which would turn the entire ghost yellow the
            # moment the line as a whole got too expensive, even for the
            # leading stretch you could still build).
            color_flags = self._drag_affordability_flags(segments)

        # Camera visibility
        cam_tile_x1, cam_tile_y1, cam_tile_x2, cam_tile_y2 = self._camera_tile_bounds()

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

        # Draw existing belts whose appearance would change
        self._draw_affected(affected_segments)

        # Draw new ghost belts
        self.ghost_renderer.draw_dragging(self.screen, self.camera, visible_segments, color_flags=visible_flags)

    def draw_delete_ghost(self, segments_to_delete):
        """Shows how nearby belts would look if the ones about to be
        deleted were actually gone."""
        affected_segments = self.belt_system.resolve_delete_preview_connections(
            segments_to_delete
        )
        self._draw_affected(affected_segments, only_if_changed=False)

    def draw_splitter_delete_ghost(self, splitter):
        """Shows how nearby belts would look if this splitter were
        actually deleted."""
        affected_segments = self.belt_system.resolve_splitter_delete_preview_connections(splitter)
        self._draw_affected(affected_segments)