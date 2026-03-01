# objects.conveyors.belt_segment
import pygame as py
from game.grid import Grid
from core.vector2 import Vector2
from objects.machines.producing_machine import ProducingMachine
from objects.machines.splitter import Splitter

class BeltSegment:
    def __init__(self, grid_pos, direction: Vector2, incoming_direction: Vector2, belt_type="basic"):
        self.grid_pos = grid_pos  # tile coordinates (x, y)
        self.direction = direction or Vector2(1, 0)
        self.incoming_direction = incoming_direction
        self.belt_type = belt_type

        # For drawing only
        self.rect = py.Rect(grid_pos[0] * Grid.CELL_SIZE,
                                grid_pos[1] * Grid.CELL_SIZE,
                                Grid.CELL_SIZE,
                                Grid.CELL_SIZE)

        # Items on this segment
        self.item = None
        self.item_progress = 0.0
        self.items_per_minute = self._get_items_per_minute_for_type()
        self.speed = (self.items_per_minute / 60)  # tiles per second (use tiles, not pixels)

    def update(self, belt_map, machines, dt):
        if not self.item:
            self._pull_from_prev_machine(machines)
            return

        # Move item along the belt in tile units
        self.item_progress += self.speed * dt
        if self.item_progress >= 1.0:
            next_pos = (self.grid_pos[0] + self.direction.x,
                        self.grid_pos[1] + self.direction.y)

            next_segment = belt_map.get(next_pos)
            moved = False

            # Move to next belt
            if next_segment and next_segment.item is None:
                if not (next_segment.direction.x == -self.direction.x and
                        next_segment.direction.y == -self.direction.y):
                    next_segment.item = self.item
                    next_segment.item_progress = 0.0
                    self._clear_item()
                    moved = True

            # Move into machine
            if not moved:
                for machine in machines:
                    if next_pos in getattr(machine, "occupied_cells", []):
                        if self._try_insert_into_machine(machine):
                            moved = True
                            break

            if not moved:
                self.item_progress = 1.0  # stop until it can move

    def draw_item(self, screen, camera):
        if not self.item or not self.item.sprite: 
            return

        # Draw interpolation based on item_progress
        start_x = self.grid_pos[0] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2
        start_y = self.grid_pos[1] * Grid.CELL_SIZE + Grid.CELL_SIZE // 2
        end_x = start_x + self.direction.x * Grid.CELL_SIZE
        end_y = start_y + self.direction.y * Grid.CELL_SIZE

        draw_x = start_x + (end_x - start_x) * self.item_progress
        draw_y = start_y + (end_y - start_y) * self.item_progress

        size = int(Grid.CELL_SIZE * 0.5)
        sprite = py.transform.scale(self.item.sprite, (size, size))
        screen.blit(sprite, (draw_x - camera.x - size // 2, draw_y - camera.y - size // 2))

    def refund_item_on_segment(self, player_inventory):
        if self.item:
            player_inventory.try_add_items(self.item.item_id, 1)
            self._clear_item()

    def _clear_item(self):
        self.item = None
        self.item_progress = 0.0

    def _pull_from_prev_machine(self, machines):
        prev_pos = (self.grid_pos[0] - self.direction.x,
                    self.grid_pos[1] - self.direction.y)
        for machine in machines:
            if isinstance(machine, ProducingMachine) and prev_pos in getattr(machine, "occupied_cells", []):
                next_item = machine.push_output_items(peek=True)
                if next_item:
                    self.item = machine.push_output_items(peek=False)
                    self.item_progress = 0.0
                    self.incoming_direction = self.direction
                break

    def _try_insert_into_machine(self, machine):
        if isinstance(machine, Splitter):
            success = machine.receive_item(self.item, incoming_direction=self.direction)
            if success: self._clear_item()
            return success

        elif isinstance(machine, ProducingMachine):
            for inv_item_id, inv in machine.input_inventories.items():
                if self.item.item_id == inv_item_id:
                    added = inv.try_add_items(self.item, 1)
                    if added:
                        self._clear_item()
                    return added
        return False
    
    def _get_items_per_minute_for_type(self):
        if self.belt_type == "basic":
            return 120
        elif self.belt_type == "fast":
            return 240
        elif self.belt_type == "express":
            return 480
        else:
            return 120  # default