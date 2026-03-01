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

    # -----------------------------
    # Place belt
    # -----------------------------
    def place_belt(self, world_x2, world_y2, belt_type="basic"):
        start_tile = (self.beltX1, self.beltY1)
        end_tile = self.world.snap_to_tile(world_x2, world_y2)

        tiles = self._get_tiles_for_drag(start_tile, end_tile, horizontal_first=self.belt_first_axis_horizontal)
        segments = self._tiles_to_segments(tiles, belt_type=belt_type)

        # Check if any tile is blocked by machines, belts, or player
        if any(self.world.is_cell_blocked(seg.grid_pos) or self.world.is_blocked_by_player(seg.grid_pos)
               for seg in segments):
            return  # Can't build here

        # Calculate total cost
        total_cost = {}
        build_cost = self.BUILD_COSTS[belt_type]
        for seg in segments:
            for item_id, amount in build_cost.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        if not self.player.inventory.has_enough_items(total_cost):
            return
        self.player.inventory.try_remove_items(total_cost)

        # Add segments to world
        for seg in segments:
            self.world.add_belt_segment(seg)

        self.update_belt_incoming_direction(segments)

    # -----------------------------
    # Delete belt
    # -----------------------------
    def delete_belt(self, mx, my, delete_whole=False, camera_x=0, camera_y=0, player_inventory=None):
        world_x, world_y = mx + camera_x, my + camera_y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target_seg = self.world.get_belt_segment_at(world_x, world_y)
        if not target_seg:
            return

        to_delete = self.get_connected_belt_segments(target_seg) if (delete_whole or shift_held) else [target_seg]

        for seg in to_delete:
            seg.refund_item_on_segment(self.player.inventory)
            for item_id, amount in self.BUILD_COSTS[seg.belt_type].items():
                player_inventory.try_add_items(item_id, amount)
            self.world.remove_belt_segment(seg)

    # -----------------------------
    # Connected belts
    # -----------------------------
    def get_connected_belt_segments(self, start_seg):
        visited = set()
        stack = [start_seg]

        while stack:
            seg = stack.pop()
            if seg in visited:
                continue
            visited.add(seg)
            x, y = seg.grid_pos

            neighbors_coords = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

            for nx, ny in neighbors_coords:
                neighbor = self.world.get_belt_segment_at(nx * self.grid.CELL_SIZE,
                                                          ny * self.grid.CELL_SIZE)
                if not neighbor or neighbor in visited:
                    continue

                # Forward connection
                if (x + seg.direction.x, y + seg.direction.y) == neighbor.grid_pos:
                    stack.append(neighbor)
                # Backward connection
                if (nx + neighbor.direction.x, ny + neighbor.direction.y) == seg.grid_pos:
                    stack.append(neighbor)

        return list(visited)

    # -----------------------------
    # Convert tiles → BeltSegments
    # -----------------------------
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

            incoming = None
            if i > 0:
                px, py = tiles[i - 1]
                x, y = tile
                incoming = Vector2(x - px, y - py)

            segments.append(BeltSegment(tile, direction, incoming, belt_type=belt_type))

        return segments

    # -----------------------------
    # Update incoming directions
    # -----------------------------
    def update_belt_incoming_direction(self, segments=None):
        targets = segments or self.world.belt_segments
        for seg in targets:
            seg.incoming_direction = self._calculate_incoming_for_segment(seg, self.world.belt_map)

    def _calculate_incoming_for_segment(self, seg, lookup_map):
        x, y = seg.grid_pos
        neighbors = [lookup_map.get((x - 1, y)), lookup_map.get((x + 1, y)),
                     lookup_map.get((x, y - 1)), lookup_map.get((x, y + 1))]

        for neighbor in neighbors:
            if not neighbor:
                continue
            nx, ny = neighbor.grid_pos
            if (nx + neighbor.direction.x, ny + neighbor.direction.y) == (x, y):
                return Vector2(x - nx, y - ny)

        return seg.direction

    # -----------------------------
    # Ghost preview connections
    # -----------------------------
    def resolve_preview_connections(self, preview_segments):
        temp_map = self.world.belt_map.copy()
        for seg in preview_segments:
            temp_map[seg.grid_pos] = seg
        for seg in preview_segments:
            seg.incoming_direction = self._calculate_incoming_for_segment(seg, temp_map)

    # -----------------------------
    # Get tiles for drag path
    # -----------------------------
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