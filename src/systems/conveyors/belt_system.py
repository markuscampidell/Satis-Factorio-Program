# systems.conveyors.belt_system
import pygame as py

from core.vector2 import Vector2
from objects.conveyors.belt_segment import BeltSegment

class BeltSystem:
    BUILD_COSTS = {"basic": {"iron_ingot": 2},
                   "fast": {"iron_ingot": 5, "copper_ingot": 1},
                   "express": {"iron_ingot": 10, "copper_ingot": 5}}
    
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

    def place_belt(self, world_x2, world_y2, belt_type="basic"):
        start_x, start_y = self._snap_to_grid(self.beltX1, self.beltY1)
        end_x, end_y = self._snap_to_grid(world_x2, world_y2)

        rects = self._get_snapped_rects_for_drag(start_x, start_y, end_x, end_y, horizontal_first=self.belt_first_axis_horizontal)
        segments, blocked = self._rects_to_segments(rects, belt_type=belt_type, check_blocked=True)
        if blocked: return

        total_cost = {}
        build_cost = self.BUILD_COSTS[belt_type]
        for seg in segments:
            for item_id, amount in build_cost.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        if not self.player.inventory.has_enough_items(total_cost): return
        self.player.inventory.try_remove_items(total_cost)

        for seg in segments:
            self.world.add_belt_segment(seg)

        self.update_belt_incoming_direction(segments)
    
    def delete_belt(self, mx, my, delete_whole=False, camera_x=0, camera_y=0, player_inventory=None): # ok
        world_x = mx + camera_x
        world_y = my + camera_y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target_seg = self.world.get_belt_segment_at(world_x, world_y)
        if not target_seg: return

        if delete_whole or shift_held: to_delete = self.get_connected_belt_segments(target_seg)
        else: to_delete = [target_seg]

        for seg in to_delete:
            seg.refund_item_on_segment(self.player.inventory)
            for item_id, amount in self.BUILD_COSTS[seg.belt_type].items():
                player_inventory.try_add_items(item_id, amount)
            self.world.remove_belt_segment(seg)
    
    def get_connected_belt_segments(self, start_seg):
        visited = set()
        stack = [start_seg]
        cell = self.grid.CELL_SIZE

        while stack:
            seg = stack.pop()
            if seg in visited: continue
            visited.add(seg)

            neighbors_coords = [(seg.rect.x + cell, seg.rect.y),
                                (seg.rect.x - cell, seg.rect.y),
                                (seg.rect.x, seg.rect.y + cell),
                                (seg.rect.x, seg.rect.y - cell)]
            for nx, ny in neighbors_coords:
                neighbor = self.world.belt_map.get((nx, ny))
                if not neighbor or neighbor in visited: continue

                if ((seg.rect.centerx + seg.direction.x * cell == neighbor.rect.centerx and
                    seg.rect.centery + seg.direction.y * cell == neighbor.rect.centery) or
                    (neighbor.rect.centerx + neighbor.direction.x * cell == seg.rect.centerx and
                    neighbor.rect.centery + neighbor.direction.y * cell == seg.rect.centery)):
                    stack.append(neighbor)

        return list(visited)
    
    def any_rect_blocked(self, rects):
        return any(self.world.is_rect_blocked(r) for r in rects)

    def _rects_to_segments(self, rects, belt_type="basic", check_blocked=False):
        segments = []
        blocked = False
        cell = self.grid.CELL_SIZE

        for i, r in enumerate(rects):
            if check_blocked and self.world.is_rect_blocked(r):
                blocked = True

            # Outgoing direction
            if len(rects) == 1:
                direction = self.belt_placement_direction
            else:
                if i < len(rects) - 1:
                    nxt = rects[i + 1]
                    direction = Vector2((nxt.x - r.x) // cell, (nxt.y - r.y) // cell)
                else:
                    prev = rects[i - 1]
                    direction = Vector2((r.x - prev.x) // cell, (r.y - prev.y) // cell)

            # Incoming direction
            incoming = None
            if i > 0:
                prev = rects[i - 1]
                incoming = Vector2((r.x - prev.x) // cell, (r.y - prev.y) // cell)

            segments.append(BeltSegment(r, direction, incoming, belt_type=belt_type))

        if check_blocked:
            return segments, blocked
        return segments
    
    def update_belt_incoming_direction(self, segments=None):
        targets = segments or self.world.belt_segments

        for seg in targets:
            seg.incoming_direction = self._calculate_incoming_for_segment(seg, self.world.belt_map)
    
    def _calculate_incoming_for_segment(self, seg, lookup_map):
        cell = self.grid.CELL_SIZE

        # Neighbors in 4 directions
        left  = lookup_map.get((seg.rect.x - cell, seg.rect.y))
        right = lookup_map.get((seg.rect.x + cell, seg.rect.y))
        up    = lookup_map.get((seg.rect.x, seg.rect.y - cell))
        down  = lookup_map.get((seg.rect.x, seg.rect.y + cell))

        for neighbor in (left, right, up, down):
            if neighbor:
                nx, ny = neighbor.rect.centerx, neighbor.rect.centery
                sx, sy = seg.rect.centerx, seg.rect.centery

                if (nx + neighbor.direction.x * cell == sx and
                    ny + neighbor.direction.y * cell == sy):

                    return Vector2(
                        seg.rect.x - neighbor.rect.x,
                        seg.rect.y - neighbor.rect.y
                    ).snapped()

        # Default: straight
        return seg.direction
    
    def resolve_preview_connections(self, preview_segments):
        # Create temporary lookup map
        temp_map = self.world.belt_map.copy()

        # Add preview segments to lookup
        for seg in preview_segments:
            temp_map[(seg.rect.x, seg.rect.y)] = seg

        # Calculate incoming using combined map
        for seg in preview_segments:
            seg.incoming_direction = self._calculate_incoming_for_segment(seg, temp_map)

    def _get_snapped_rects_for_drag(self, start_x, start_y, end_x, end_y, horizontal_first=True):
        start_x, start_y = self._snap_to_grid(start_x, start_y)
        end_x, end_y = self._snap_to_grid(end_x, end_y)
        cell = self.grid.CELL_SIZE

        rects = []
        dx = 1 if end_x >= start_x else -1
        dy = 1 if end_y >= start_y else -1

        if horizontal_first:
            for x in range(start_x, end_x + dx * cell, dx * cell): rects.append(py.Rect(x, start_y, cell, cell))
            for y in range(start_y + dy * cell, end_y + dy * cell, dy * cell): rects.append(py.Rect(end_x, y, cell, cell))
        else:
            for y in range(start_y, end_y + dy * cell, dy * cell): rects.append(py.Rect(start_x, y, cell, cell))
            for x in range(start_x + dx * cell, end_x + dx * cell, dx * cell): rects.append(py.Rect(x, end_y, cell, cell))

        return rects

    def _snap_to_grid(self, x, y):
            cell = self.grid.CELL_SIZE
            return (int(x // cell) * cell, int(y // cell) * cell)