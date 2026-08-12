# systems.conveyors.belt_system
import pygame as py
from core.vector2 import Vector2
from objects.conveyors.belt_segment import BeltSegment

class BeltSystem:
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

        self.belt_first_axis_horizontal = True
        self.beltX1 = 0
        self.beltY1 = 0
        self.placing_belt = False
        self.selected_belt_type = "basic"
        self.belt_placement_direction = Vector2(1, 0)

    def is_tile_blocked_for_placement(self, grid_pos, allow_replace):
        """The player always blocks belt placement. A machine or existing
        belt tile only blocks if we're not allowed to replace it (shift
        held) - shift replaces everything, belts and machines alike."""
        if self.world.is_blocked_by_player(grid_pos):
            return True
        return self.world.is_cell_blocked(grid_pos) and not allow_replace

    def get_placement_modifiers(self):
        """Shift held means replace everything under the belt path -
        existing belts and machines alike."""
        return bool(py.key.get_mods() & py.KMOD_SHIFT)

    @classmethod
    def apply_refunds(cls, inventory, replaced_segments, replaced_machines):
        """Try to add every refund (belt items+costs, machine contents) to
        `inventory`. Returns False the instant something doesn't fit,
        without adding anything further. Works the same against a scratch
        clone (dry run) or the real inventory (commit)."""
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
        """What placing `segments` (as `belt_type`) would replace: the
        existing belts and machines under the path, and the total cost of
        the new belts. Used both to actually place them and to preview
        whether placing them would succeed."""
        cells = [seg.grid_pos for seg in segments]
        replaced_segments, replaced_machines = self.world.gather_occupants(cells)

        total_cost = {}
        build_cost = self.BUILD_COSTS[belt_type]
        for seg in segments:
            for item_id, amount in build_cost.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        return replaced_segments, replaced_machines, total_cost

    def check_placement_affordability(self, replaced_segments, replaced_machines, total_cost):
        """Dry-runs the refund+cost sequence on a scratch copy of the
        inventory - the same all-or-nothing rule place_belt enforces for
        real. Returns:
        - "no_space" if a refund (belt items, belt costs, machine costs,
          machine contents) wouldn't fit in the inventory,
        - "no_funds" if everything fits but the net cost isn't affordable,
        - "ok" if the placement would succeed.
        Split into a status rather than a plain bool so previews can show
        *why* it would fail (orange = no space, yellow = can't afford)."""
        scratch = self.player.inventory.clone()
        if not self.apply_refunds(scratch, replaced_segments, replaced_machines):
            return "no_space"
        return "ok" if scratch.try_remove_items(total_cost) else "no_funds"

    def place_belt(self, world_x2, world_y2, belt_type="basic"):
        start_tile = (self.beltX1, self.beltY1)
        end_tile = self.world.snap_to_tile(world_x2, world_y2)

        tiles = self._get_tiles_for_drag(start_tile, end_tile, horizontal_first=self.belt_first_axis_horizontal)
        segments = self._tiles_to_segments(tiles, belt_type=belt_type)

        allow_replace = self.get_placement_modifiers()

        if any(self.is_tile_blocked_for_placement(seg.grid_pos, allow_replace) for seg in segments):
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
        """True if the player's inventory has room for everything deleting
        all of `segments` would refund (their build cost plus any item
        mid-transit on them)."""
        scratch = self.player.inventory.clone()
        return self.apply_refunds(scratch, segments, [])

    def delete_belt(self, mx, my, delete_whole=False, camera_x=0, camera_y=0, player_inventory=None):
        world_x, world_y = mx + camera_x, my + camera_y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target_seg = self.world.get_belt_segment_at(world_x, world_y)
        if not target_seg:
            return

        to_delete = self.get_connected_belt_segments(target_seg) if (delete_whole or shift_held) else [target_seg]

        if not self.can_afford_belt_deletion(to_delete):
            return  # Not enough inventory space to receive the refund

        for seg in to_delete:
            seg.refund_item_on_segment(self.player.inventory)
            for item_id, amount in self.BUILD_COSTS[seg.belt_type].items():
                player_inventory.try_add_items(item_id, amount)
            self.world.remove_belt_segment(seg)

        self.update_belt_incoming_directions()

    def get_connected_belt_segments(self, start_seg):
        visited = set()
        stack = [start_seg]

        while stack:
            seg = stack.pop()

            if seg in visited:
                continue

            visited.add(seg)

            x, y = seg.grid_pos

            neighbors_coords = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1)
            ]

            for nx, ny in neighbors_coords:
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
            seg.incoming_directions = self._calculate_incoming_for_segment(
                seg, self.world.belt_map
            )

    def _calculate_incoming_for_segment(self, seg, lookup_map):
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

        # Fallback for isolated belts
        if not incoming_directions:
            incoming_directions.append(seg.direction)

        return incoming_directions
    
    def resolve_preview_connections(self, preview_segments):
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

            for pos in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ):
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

    def resolve_delete_preview_connections(self, segments_to_delete):
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

            for pos in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ):
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