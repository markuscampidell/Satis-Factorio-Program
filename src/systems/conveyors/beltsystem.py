import pygame as py

from core.vector2 import Vector2
from objects.conveyors.conveyor_belt import BeltSegment

class BeltSystem:
    BUILD_COSTS = {"basic": {"iron_ingot": 2},
                   "fast": {"iron_ingot": 5, "copper_ingot": 1},
                   "express": {"iron_ingot": 10, "copper_ingot": 5}}
    
    def __init__(self, world, grid, player, screen, camera, screen_width, screen_height, ghost_belt_renderer):
        self.world = world
        self.grid = grid
        self.player = player
        self.screen = screen
        self.camera = camera
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ghost_belt_renderer = ghost_belt_renderer  # <--- set it here
        self.belt_first_axis_horizontal = True
        self.beltX1 = 0
        self.beltY1 = 0
        self.belt_placement_direction = Vector2(1, 0)

    def place_belt(self, world_x2, world_y2, belt_type="basic"):
        start_x, start_y = self._snap_to_grid(self.beltX1, self.beltY1)
        end_x, end_y = self._snap_to_grid(world_x2, world_y2)

        rects = self._get_snapped_rects_for_drag(start_x, start_y, end_x, end_y, horizontal_first=self.belt_first_axis_horizontal)

        # Convert rects into segments
        segments, blocked = self._rects_to_segments(rects, belt_type=belt_type, check_blocked=True)
        if blocked: return

        # Calculate total cost
        total_cost = {}
        build_cost = self.BUILD_COSTS[belt_type]
        for seg in segments:
            for item_id, amount in build_cost.items():
                total_cost[item_id] = total_cost.get(item_id, 0) + amount

        if not self.player.inventory.has_enough_items(total_cost): return
        
        self.player.inventory.try_remove_items(total_cost)

        self.world.belt_segments.extend(segments)
        for seg in segments:
            self.world.belt_map[seg.rect.topleft] = seg

        self.recalc_belt_directions(segments)
        self.update_belt_sprites(segments)
        self.update_belt_incoming_direction(segments)

    
    def delete_belt(self, mx, my, delete_whole=False, camera_x=0, camera_y=0, player_inventory=None): # ok
        world_x = mx + camera_x
        world_y = my + camera_y
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        target_seg = None
        for seg in self.world.belt_segments:
            if seg.rect.collidepoint(world_x, world_y):
                target_seg = seg
                break
        if not target_seg: return

        if delete_whole or shift_held: to_delete = self.get_connected_belt_segments(target_seg)
        else: to_delete = [target_seg]

        for seg in to_delete:
            seg.refund_item_on_segment(self.player.inventory)
            for item_id, amount in self.BUILD_COSTS[seg.belt_type].items():
                player_inventory.try_add_items(item_id, amount)
            self.remove_segment_from_map(seg)


    def recalc_belt_directions(self, segments=None):
        cell = self.grid.CELL_SIZE
        segments = segments or self.world.belt_segments

        for seg in segments:
            # If single segment, just use placement direction
            if len(segments) == 1:
                seg.direction = self.belt_placement_direction
                continue

            # Find the next segment in line
            neighbors = {(1, 0): self.world.belt_map.get((seg.rect.x + cell, seg.rect.y)),
                         (-1, 0): self.world.belt_map.get((seg.rect.x - cell, seg.rect.y)),
                         (0, 1): self.world.belt_map.get((seg.rect.x, seg.rect.y + cell)),
                         (0, -1): self.world.belt_map.get((seg.rect.x, seg.rect.y - cell))}

            current_dir = (seg.direction.x, seg.direction.y)
            next_seg = neighbors.get(current_dir)

            if next_seg:
                # Set direction toward next segment
                dx = (next_seg.rect.x - seg.rect.x) // cell
                dy = (next_seg.rect.y - seg.rect.y) // cell
                seg.direction = Vector2(dx, dy)
    
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



    def update_belt_sprites(self, segments=None):
        """
        Updates sprite_type for belt segments based on neighbors.
        Only affects visuals, not direction.
        """
        cell = self.grid.CELL_SIZE
        targets = segments or self.world.belt_segments

        for seg in targets:
            seg.sprite_type = "straight"  # default

            # Get front neighbor
            fx = seg.rect.x + seg.direction.x * cell
            fy = seg.rect.y + seg.direction.y * cell
            front = self.world.belt_map.get((fx, fy))

            if front and (front.direction.x != seg.direction.x or front.direction.y != seg.direction.y):
                # front neighbor is orthogonal → possible curve
                # check side neighbors
                left_dx, left_dy = -seg.direction.y, seg.direction.x
                right_dx, right_dy = seg.direction.y, -seg.direction.x
                left_neighbor = self.world.belt_map.get((seg.rect.x + left_dx*cell, seg.rect.y + left_dy*cell))
                right_neighbor = self.world.belt_map.get((seg.rect.x + right_dx*cell, seg.rect.y + right_dy*cell))

                if left_neighbor and not right_neighbor:
                    seg.sprite_type = "curve_left"
                elif right_neighbor and not left_neighbor:
                    seg.sprite_type = "curve_right"
    
    def update_belt_incoming_direction(self, segments=None):
        """
        #Updates only the *incoming_direction* used for drawing curves.
        #Does NOT change the actual movement direction of the belt.
        """
        cell = self.grid.CELL_SIZE
        targets = segments or self.world.belt_segments

        for seg in targets:
            # Check neighbors in all 4 directions
            left  = self.world.belt_map.get((seg.rect.x - cell, seg.rect.y))
            right = self.world.belt_map.get((seg.rect.x + cell, seg.rect.y))
            up    = self.world.belt_map.get((seg.rect.x, seg.rect.y - cell))
            down  = self.world.belt_map.get((seg.rect.x, seg.rect.y + cell))

            # Determine incoming visually
            # If there is a neighbor whose outgoing points to this segment, use that
            incoming = None
            for neighbor in (left, right, up, down):
                if neighbor:
                    nx, ny = neighbor.rect.centerx, neighbor.rect.centery
                    sx, sy = seg.rect.centerx, seg.rect.centery
                    if (nx + neighbor.direction.x * cell == sx and
                        ny + neighbor.direction.y * cell == sy):
                        incoming = Vector2(seg.rect.x - neighbor.rect.x, seg.rect.y - neighbor.rect.y).snapped()
                        break

            if incoming:
                seg.incoming_direction = incoming
            else:
                # No neighbor feeding this belt → straight sprite
                seg.incoming_direction = seg.direction



    def rebuild_belt_map(self):
        self.world.belt_map = {seg.rect.topleft: seg for seg in self.world.belt_segments}
    
    def remove_segment_from_map(self, seg):
        if seg in self.world.belt_segments:
            self.world.belt_segments.remove(seg)
        self.world.belt_map.pop(seg.rect.topleft, None)

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

    def ghost_conveyor_belt(self, selected_machine_class, placing_belt=False, selected_belt_type="basic"):
        if selected_machine_class is not BeltSegment: return

        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.screen_width, self.screen_height)

        if not placing_belt:
            snapped_x, snapped_y = self._snap_to_grid(world_x, world_y)
            temp_rect = py.Rect(snapped_x, snapped_y, self.grid.CELL_SIZE, self.grid.CELL_SIZE)

            if temp_rect.colliderect(camera_rect):
                if self.world.is_rect_blocked(temp_rect): color_flag = "red"
                elif self.player.inventory.has_enough_items(self.BUILD_COSTS[selected_belt_type]): color_flag = "normal"
                else: color_flag = "yellow"

                direction = (self.belt_placement_direction or Vector2(1, 0)).snapped()
                self.ghost_belt_renderer.draw_single(self.screen, self.camera, snapped_x, snapped_y, direction, direction, color_flag)
            return

        rects = self._get_snapped_rects_for_drag(self.beltX1, self.beltY1, world_x, world_y, horizontal_first=self.belt_first_axis_horizontal)
        segments = self._rects_to_segments(rects, belt_type=selected_belt_type)

        any_blocked = any(self.world.is_rect_blocked(rect) for rect in rects)

        available = {item_id: self.player.inventory.get_amount(item_id) for item_id in self.BUILD_COSTS[selected_belt_type]}

        color_flags = []
        for seg in segments:
            if any_blocked:
                color_flags.append("red")
                continue
            can_build = all(available[item_id] >= cost for item_id, cost in self.BUILD_COSTS[seg.belt_type].items())
            if can_build:
                color_flags.append("normal")
                for item_id, cost in self.BUILD_COSTS[seg.belt_type].items():
                    available[item_id] -= cost
            else:
                color_flags.append("yellow")

        visible_segments = []
        visible_flags = []

        for seg, flag in zip(segments, color_flags):
            if seg.rect.colliderect(camera_rect):
                visible_segments.append(seg)
                visible_flags.append(flag)

        self.ghost_belt_renderer.draw_dragging(self.screen, self.camera, visible_segments, color_flags=visible_flags)

    def _snap_to_grid(self, x, y):
            cell = self.grid.CELL_SIZE
            return (int(x // cell) * cell, int(y // cell) * cell)