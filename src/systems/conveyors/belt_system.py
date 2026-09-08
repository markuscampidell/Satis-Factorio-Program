# systems.conveyors.belt_system
import pygame as py
from core.vector2 import Vector2
from game.grid import four_neighbor_coords
from objects.conveyors.belt_segment import BeltSegment

class BeltSystem:
    """Handles everything about placing and deleting conveyor belts -
    dragging out a line of them, figuring out which way each one should
    face, and refunding what they cost when they're removed."""

    BUILD_COSTS = {
        "basic": {"iron_ingot": 2},
        "fast": {"iron_ingot": 5, "copper_ingot": 1},
        "express": {"iron_ingot": 10, "copper_ingot": 5}
    }

    def __init__(self, world, grid, player, ghost_belt_renderer):
        self.world = world
        self.grid = grid
        self.player = player
        self.ghost_belt_renderer = ghost_belt_renderer

        self.beltX1 = 0
        self.beltY1 = 0
        self.placing_belt = False
        self.selected_belt_type = "express"
        self.belt_placement_direction = Vector2(1, 0)

    def is_tile_blocked_for_placement(self, grid_pos, allow_replace):
        if self.world.is_blocked_by_player(grid_pos):
            return True
        return self.world.is_cell_blocked(grid_pos) and not allow_replace

    def _segment_matches_existing(self, seg, require_type):
        """True if there's already a belt at seg's tile facing the same
        direction as seg (and, if require_type, also the same belt_type) -
        i.e. placing seg there would be a genuine no-op, or close to one."""
        existing = self.world.belt_map.get(seg.grid_pos)
        if existing is None:
            return False
        if existing.direction != seg.direction:
            return False
        if require_type and existing.belt_type != seg.belt_type:
            return False
        return True

    def _new_incoming_directions(self, segments):
        """The flow direction arriving at each tile of a dragged line, in
        order - tile i's incoming is tile (i-1)'s outgoing, the same hop
        _tiles_to_segments already used to work out tile (i-1)'s own
        direction. The start tile (index 0) has nothing before it in this
        drag to define an incoming side, so it's None there."""
        incoming = [None]
        for i in range(1, len(segments)):
            incoming.append(segments[i - 1].direction)
        return incoming

    def _segment_reverses_existing(self, seg, new_incoming):
        """True if there's already a belt at seg's tile whose flow is the
        exact reverse of what's being dragged through it here - not just
        facing the opposite way, but actually swapping entry and exit: the
        existing belt's outgoing matches the new flow's incoming, and its
        (single) incoming matches the new outgoing. A straight belt's
        incoming and outgoing are the same direction, so this reduces to
        a plain head-on reversal for those; a curve needs both ends to
        swap correctly, which is why outgoing-only comparison isn't
        enough. Only applies when the existing belt has exactly one
        incoming side - reversing a merge point (multiple inputs) is
        ambiguous, so that still needs Shift. `new_incoming` is None for
        the drag's own start tile, which doesn't use this check at all
        (see is_drag_tile_blocked)."""
        if new_incoming is None:
            return False
        existing = self.world.belt_map.get(seg.grid_pos)
        if existing is None or len(existing.incoming_directions) != 1:
            return False
        existing_in = existing.incoming_directions[0]
        return seg.direction == -existing_in and new_incoming == -existing.direction

    def _tile_auto_replaceable(self, seg, new_incoming):
        """Whether this one tile is fine to place on without Shift on its
        own merits - empty, an exact match, or a clean reversal. Doesn't
        cover the drag's start tile's own separate always-replace
        exemption (see is_drag_tile_blocked) - this is only about a tile
        standing on its own."""
        return (
            not self.world.is_cell_blocked(seg.grid_pos)
            or self._segment_matches_existing(seg, require_type=True)
            or self._segment_reverses_existing(seg, new_incoming)
        )

    def _others_free_or_direction_matching(self, segments, start_tile):
        """Whether every tile in a dragged line OTHER than the start tile
        is itself already fine to place on without Shift (empty, an exact
        match, or a reversal) - the qualifying condition for the start
        tile's own always-replace exemption below."""
        return all(
            seg.grid_pos == start_tile or self._tile_auto_replaceable(seg, new_incoming)
            for seg, new_incoming in zip(segments, self._new_incoming_directions(segments))
        )

    def is_drag_tile_blocked(self, seg, new_incoming, start_tile, others_ok, allow_replace):
        """Whether this one tile of a dragged belt line still needs Shift
        held to place, under the auto-replace rules: an empty tile never
        needs it; Shift held always overrides everything (except the
        player's own tile); the drag's start tile replaces an existing
        BELT there for free as long as the rest of the line is itself
        either empty or already fine on its own (not a machine, and not
        when the rest of the drag would still need Shift for something
        else anyway); any other tile skips Shift if what's there already
        matches (same direction and belt_type - a true no-op) or is the
        exact reverse of the new flow through it (see
        _segment_reverses_existing)."""
        if self.world.is_blocked_by_player(seg.grid_pos):
            return True
        if allow_replace:
            return False
        if not self.world.is_cell_blocked(seg.grid_pos):
            return False
        if seg.grid_pos == start_tile:
            return not (self.world.belt_map.get(seg.grid_pos) is not None and others_ok)
        return not (self._segment_matches_existing(seg, require_type=True)
                    or self._segment_reverses_existing(seg, new_incoming))

    def get_placement_modifiers(self):
        """Shift held means replace everything under the belt path -
        existing belts and machines alike."""
        return bool(py.key.get_mods() & py.KMOD_SHIFT)

    @classmethod
    def apply_refunds(cls, inventory, replaced_segments, replaced_machines):
        """Gives back everything these belts/machines are worth - any item
        sitting on them, plus what they originally cost to build - into an
        inventory. Works just as well on a throwaway copy of the
        inventory, so it can also be used to check affordability without
        changing anything for real."""
        for seg in replaced_segments:
            if seg.item and not inventory.try_add_items(seg.item.item_id, 1):
                return False
            for item_id, amount in cls.BUILD_COSTS[seg.belt_type].items():
                if not inventory.try_add_items(item_id, amount):
                    return False

        for machine in replaced_machines:
            for item_id, amount in machine.get_refund_items().items():
                if not inventory.try_add_items(item_id, amount):
                    return False

        return True

    def gather_replacements(self, segments, belt_type):
        """Works out what would get replaced - and what it would cost - if
        these belt tiles were built on top of whatever's already there."""
        cells = [seg.grid_pos for seg in segments]
        replaced_segments, replaced_machines = self.world.gather_occupants(cells)

        total_cost = {}
        build_cost = self.BUILD_COSTS[belt_type]
        for seg in segments:
            for item_id, amount in build_cost.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        return replaced_segments, replaced_machines, total_cost

    def check_placement_affordability(self, replaced_segments, replaced_machines, total_cost):
        """Checks whether building here would actually work: enough room
        for the refund from whatever gets replaced, and enough items left
        over afterward to pay the build cost."""
        scratch = self.player.inventory.clone()
        if not self.apply_refunds(scratch, replaced_segments, replaced_machines):
            return "no_space"
        return "ok" if scratch.try_remove_items(total_cost) else "no_funds"

    def get_drag_tiles(self, start_tile, end_tile):
        """Works out the line of tiles between two points when dragging
        out a belt, flipping the order if you dragged backwards from the
        direction the belt is actually supposed to flow."""
        x1, y1 = start_tile
        x2, y2 = end_tile
        direction = self.belt_placement_direction

        horizontal_first = direction.x != 0
        reversed_flow = False

        if horizontal_first and x2 != x1:
            drag_sign = 1 if x2 > x1 else -1
            facing_sign = 1 if direction.x > 0 else -1
            reversed_flow = drag_sign != facing_sign
        elif not horizontal_first and y2 != y1:
            drag_sign = 1 if y2 > y1 else -1
            facing_sign = 1 if direction.y > 0 else -1
            reversed_flow = drag_sign != facing_sign

        tiles = self._get_tiles_for_drag(start_tile, end_tile, horizontal_first=horizontal_first)
        return list(reversed(tiles)) if reversed_flow else tiles

    def place_belt(self, world_x2, world_y2, belt_type="basic"):
        """Actually builds a dragged line of belts, after checking the
        whole thing fits and is affordable - it's all or nothing, never
        just some of the belts."""
        start_tile = (self.beltX1, self.beltY1)
        end_tile = self.world.snap_to_tile(world_x2, world_y2)

        tiles = self.get_drag_tiles(start_tile, end_tile)
        segments = self._tiles_to_segments(tiles, belt_type=belt_type)

        allow_replace = self.get_placement_modifiers()
        others_ok = self._others_free_or_direction_matching(segments, start_tile)
        new_incomings = self._new_incoming_directions(segments)

        if any(self.is_drag_tile_blocked(seg, new_in, start_tile, others_ok, allow_replace)
               for seg, new_in in zip(segments, new_incomings)):
            return  # Can't build here

        replaced_segments, replaced_machines, total_cost = self.gather_replacements(segments, belt_type)

        # Simulate the whole operation first - no lost items, no partial
        # placement if anything doesn't fit or isn't affordable.
        if self.check_placement_affordability(replaced_segments, replaced_machines, total_cost) != "ok":
            return

        # Simulation succeeded exactly as it will for real - apply it.
        self.apply_refunds(self.player.inventory, replaced_segments, replaced_machines)
        for old_seg in replaced_segments:
            old_seg._clear_item()
            self.world.remove_belt_segment(old_seg)
        for machine in replaced_machines:
            self.world.remove_machine(machine)

        self.player.inventory.try_remove_items(total_cost)

        # Add segments to world
        for seg in segments:
            self.world.add_belt_segment(seg)

        self.update_belt_incoming_directions()

    def can_afford_belt_deletion(self, segments):
        scratch = self.player.inventory.clone()
        return self.apply_refunds(scratch, segments, [])

    def delete_belt(self, mx, my, delete_whole=False, camera_x=0, camera_y=0):
        """Deletes the belt under the mouse - or, if asked, its whole
        connected run at once - and refunds the player for it. Returns
        True if anything was actually deleted, False otherwise - lets a
        click-and-drag caller retry the same tile later instead of writing
        off a merely-blocked attempt as done."""
        world_x, world_y = mx + camera_x, my + camera_y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target_seg = self.world.get_belt_segment_at(world_x, world_y)
        if not target_seg:
            return False

        to_delete = self.get_connected_belt_segments(target_seg) if (delete_whole or shift_held) else [target_seg]

        if not self.can_afford_belt_deletion(to_delete):
            return False  # Not enough inventory space to receive the refund

        for seg in to_delete:
            seg.refund_item_on_segment(self.player.inventory)
            for item_id, amount in self.BUILD_COSTS[seg.belt_type].items():
                self.player.inventory.try_add_items(item_id, amount)
            self.world.remove_belt_segment(seg)

        self.update_belt_incoming_directions()
        return True

    def get_connected_belt_segments(self, start_seg):
        """Finds every belt connected to this one, following the belt line
        outward in every direction - used for deleting a whole run of
        belts at once."""
        visited = set()
        stack = [start_seg]

        while stack:
            seg = stack.pop()

            if seg in visited:
                continue

            visited.add(seg)

            x, y = seg.grid_pos

            for nx, ny in four_neighbor_coords(x, y):
                neighbor = self.world.get_belt_segment_at(
                    nx * self.grid.CELL_SIZE,
                    ny * self.grid.CELL_SIZE
                )

                if not neighbor or neighbor in visited:
                    continue

                if self._belts_are_connected(seg, neighbor):
                    stack.append(neighbor)

        return list(visited)

    def _belts_are_connected(self, a, b):
        """Checks if two belts actually link up (one feeds into the
        other). Two belts facing straight into each other head-on don't
        count as connected."""
        ax, ay = a.grid_pos
        bx, by = b.grid_pos

        a_points_to_b = (
            ax + a.direction.x,
            ay + a.direction.y
        ) == (bx, by)

        b_points_to_a = (
            bx + b.direction.x,
            by + b.direction.y
        ) == (ax, ay)

        # Two opposing belts are not a valid connection.
        if a_points_to_b and b_points_to_a:
            return False

        return a_points_to_b or b_points_to_a
    
    def _tiles_to_segments(self, tiles, belt_type="basic"):
        """Turns a line of tile positions into actual belt segments, each
        one facing toward whichever tile comes next in the line."""
        segments = []

        for i, tile in enumerate(tiles):
            if len(tiles) == 1:
                direction = self.belt_placement_direction
            else:
                if i < len(tiles) - 1:
                    nx, ny = tiles[i + 1]
                    x, y = tile
                    direction = Vector2(nx - x, ny - y)
                else:
                    px, py = tiles[i - 1]
                    x, y = tile
                    direction = Vector2(x - px, y - py)

            segments.append(BeltSegment(tile, direction, [], belt_type=belt_type))

        return segments



    def update_belt_incoming_directions(self, segments=None):
        targets = segments or self.world.belt_segments

        for seg in targets:
            # current_input_index points into the *old* incoming_directions
            # list, at whichever side round-robin fairness is about to
            # favor next. Recomputing the list (e.g. a neighboring belt was
            # just deleted) can shrink or reorder it, so remember which
            # actual direction the index meant before overwriting it -
            # otherwise a stale index either points at the wrong side after
            # a reorder, or is out of range entirely and crashes
            # resolve_input_requests() the next time it's used.
            old_directions = seg.incoming_directions
            old_priority_direction = (
                old_directions[seg.current_input_index]
                if 0 <= seg.current_input_index < len(old_directions)
                else None
            )

            seg.incoming_directions = self._calculate_incoming_for_segment(
                seg, self.world.belt_map
            )

            # Keep favoring the same physical side if it still feeds this
            # segment (even if it moved to a different index); only reset
            # to the default (0) if that side is the one that just
            # disappeared - e.g. the neighboring belt was deleted.
            if old_priority_direction is not None and old_priority_direction in seg.incoming_directions:
                seg.current_input_index = seg.incoming_directions.index(old_priority_direction)
            else:
                seg.current_input_index = 0

    def _calculate_incoming_for_segment(self, seg, lookup_map, extra_machines=None, exclude_machines=None):
        """Works out every direction something could currently feed into
        this belt tile from - other belts, machines, and splitters all
        count a bit differently. Used both to pick the right belt picture
        and to decide which side gets priority when more than one thing
        feeds the same tile."""
        x, y = seg.grid_pos

        neighbors = [lookup_map.get((x - 1, y)),
                     lookup_map.get((x + 1, y)),
                     lookup_map.get((x, y - 1)),
                     lookup_map.get((x, y + 1))]

        incoming_directions = []

        for neighbor in neighbors:
            if not neighbor:
                continue

            nx, ny = neighbor.grid_pos

            # Check if this neighbor points into this segment
            if (nx + neighbor.direction.x, ny + neighbor.direction.y) == (x, y):
                incoming_direction = Vector2(x - nx, y - ny)

                if incoming_direction != -seg.direction:
                    incoming_directions.append(incoming_direction)

        # extra_machines lets a preview include a machine/splitter that
        # isn't actually in the world yet (e.g. a hovered placement ghost).
        # exclude_machines lets a preview act as if a real one were already
        # gone (e.g. a hovered deletion target).
        excluded = exclude_machines or []
        all_machines = [m for m in self.world.machines if m not in excluded] + list(extra_machines or [])

        # A machine pushing into this segment only ever succeeds when the
        # segment faces directly away from it (ProducingMachine.push_output
        # requires an exact direction match) - so the only valid incoming
        # entry a machine can contribute is the segment's own direction.
        for machine in all_machines:
            get_output_tiles = getattr(machine, "_get_output_tiles", None)
            if get_output_tiles is None:
                continue

            for (dx, dy), push_direction in get_output_tiles():
                if (machine.grid_pos[0] + dx, machine.grid_pos[1] + dy) != (x, y):
                    continue

                if push_direction == seg.direction and push_direction not in incoming_directions:
                    incoming_directions.append(push_direction)

        # A splitter accepts any orientation except facing directly back
        # into it (Splitter.push_item), so unlike a machine it can
        # contribute a perpendicular direction too - same exclusion rule
        # as belts feeding each other.
        for splitter in all_machines:
            get_relative_dirs = getattr(splitter, "_get_relative_dirs", None)
            if get_relative_dirs is None:
                continue

            for push_direction in get_relative_dirs():
                tile = (
                    splitter.grid_pos[0] + int(push_direction.x),
                    splitter.grid_pos[1] + int(push_direction.y)
                )
                if tile != (x, y):
                    continue

                if push_direction != -seg.direction and push_direction not in incoming_directions:
                    incoming_directions.append(push_direction)

        # Fallback for isolated belts
        if not incoming_directions:
            incoming_directions.append(seg.direction)

        return incoming_directions
    
    def resolve_preview_connections(self, preview_segments):
        """Pretends a set of ghost belts already exist, and works out how
        they - and any real belts next to them - would actually connect.
        Used to preview a belt before you've actually placed it."""
        temp_map = self.world.belt_map.copy()

        ghost_positions = {seg.grid_pos for seg in preview_segments}

        # Add ghost belts to temporary map
        for seg in preview_segments:
            temp_map[seg.grid_pos] = seg

        # Calculate ghost belt connections
        for seg in preview_segments:
            seg.incoming_directions = self._calculate_incoming_for_segment(
                seg, temp_map
            )

        # Find existing belts affected by the preview
        affected_positions = set()

        for seg in preview_segments:
            x, y = seg.grid_pos

            for pos in four_neighbor_coords(x, y):
                if pos in self.world.belt_map and pos not in ghost_positions:
                    affected_positions.add(pos)

        # Calculate their temporary incoming directions
        affected_segments = []

        for pos in affected_positions:
            seg = self.world.belt_map[pos]

            incoming = self._calculate_incoming_for_segment(
                seg, temp_map
            )

            affected_segments.append((seg, incoming))

        return affected_segments

    def _splitter_affected_belt_positions(self, splitter):
        """Finds every belt tile touching one of a splitter's three output
        sides."""
        positions = set()

        for push_direction in splitter._get_relative_dirs():
            tile = (
                splitter.grid_pos[0] + int(push_direction.x),
                splitter.grid_pos[1] + int(push_direction.y)
            )
            if tile in self.world.belt_map:
                positions.add(tile)

        return positions

    def resolve_splitter_preview_connections(self, temp_splitter):
        """Works out how belts around a splitter would connect if it were
        placed here - used for the placement preview."""
        affected_segments = []

        for pos in self._splitter_affected_belt_positions(temp_splitter):
            seg = self.world.belt_map[pos]

            incoming = self._calculate_incoming_for_segment(
                seg, self.world.belt_map, extra_machines=[temp_splitter]
            )

            affected_segments.append((seg, incoming))

        return affected_segments

    def resolve_splitter_delete_preview_connections(self, splitter):
        """Works out how belts around a splitter would reconnect if it
        were deleted - used for the delete preview."""
        affected_segments = []

        for pos in self._splitter_affected_belt_positions(splitter):
            seg = self.world.belt_map[pos]

            incoming = self._calculate_incoming_for_segment(
                seg, self.world.belt_map, exclude_machines=[splitter]
            )

            affected_segments.append((seg, incoming))

        return affected_segments

    def resolve_delete_preview_connections(self, segments_to_delete):
        """Works out how the belts around a group of belts would look if
        those belts were deleted - used for the delete preview, only
        reporting the ones that would actually look different."""
        delete_positions = {
            seg.grid_pos for seg in segments_to_delete
        }

        # Temporary map without the belts being deleted
        temp_map = {
            pos: seg
            for pos, seg in self.world.belt_map.items()
            if pos not in delete_positions
        }

        affected_segments = []

        # Find neighbors around the belts being deleted
        affected_positions = set()

        for seg in segments_to_delete:
            x, y = seg.grid_pos

            for pos in four_neighbor_coords(x, y):
                if pos in temp_map:
                    affected_positions.add(pos)

        # Calculate how those neighbors would look
        # after the deletion.
        for pos in affected_positions:
            seg = temp_map[pos]

            incoming = self._calculate_incoming_for_segment(
                seg,
                temp_map
            )

            if incoming != seg.incoming_directions:
                affected_segments.append(
                    (seg, incoming)
                )

        return affected_segments

    def _get_tiles_for_drag(self, start_tile, end_tile, horizontal_first=True):
        """Builds an L-shaped path of tiles between two points, going
        horizontal first or vertical first depending on which way the belt
        is facing."""
        x1, y1 = start_tile
        x2, y2 = end_tile
        tiles = []
        dx = 1 if x2 >= x1 else -1
        dy = 1 if y2 >= y1 else -1

        if horizontal_first:
            for x in range(x1, x2 + dx, dx):
                tiles.append((x, y1))
            for y in range(y1 + dy, y2 + dy, dy):
                tiles.append((x2, y))
        else:
            for y in range(y1, y2 + dy, dy):
                tiles.append((x1, y))
            for x in range(x1 + dx, x2 + dx, dx):
                tiles.append((x, y2))

        return tiles