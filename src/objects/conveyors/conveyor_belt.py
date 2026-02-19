import pygame as py
from game.grid import Grid
from core.vector2 import Vector2
from objects.machines.producing_machine import ProducingMachine
from objects.machines.splitter import Splitter

class BeltSegment:
    def __init__(self, rect: py.Rect, direction: Vector2, incoming_direction: Vector2, belt_type="basic"):
        self.rect = rect
        self.direction = direction if direction else Vector2(1, 0)
        self.incoming_direction = incoming_direction
        self.belt_type = belt_type

        self.item = None
        self.item_progress = 0.0
        self.items_per_minute = self._get_items_per_minute_for_type()
        self.speed = (self.items_per_minute / 60) * Grid.CELL_SIZE  # pixels per second

    def _get_items_per_minute_for_type(self):
        if self.belt_type == "basic": return 120
        if self.belt_type == "fast": return 240
        if self.belt_type == "express": return 480

    def update(self, belt_map, machines, cell_size, dt): # ok
        if self.item:
            self.item_progress += self.speed * dt / cell_size
            if self.item_progress >= 1.0:
                next_rect = self.rect.move(int(self.direction.x * cell_size), int(self.direction.y * cell_size)) # move self.rect one tile in the direction of the segment
                next_segment = belt_map.get(next_rect.topleft)
                moved = False

                if next_segment and next_segment.item is None:
                    if not (next_segment.direction.x == -self.direction.x and next_segment.direction.y == -self.direction.y): # prevent moving into a belt going the opposite direction
                        next_segment.item = self.item
                        next_segment.item_progress = 0.0
                        self._clear_item()
                        moved = True

                if not moved:
                    for machine in machines:
                        if machine.rect.colliderect(next_rect):
                            if self._try_insert_into_machine(machine):
                                moved = True
                                break
                if not moved:
                    self.item_progress = 1.0 # stop at end of belt until it can move forward

        elif self.item is None:
            self._pull_from_prev_machine(machines, cell_size)

    def draw_item(self, screen, camera, cell_size): # ok
        if not self.item or self.item.sprite is None: return

        incoming = self.incoming_direction or self.direction
        center_x = self.rect.x + cell_size // 2
        center_y = self.rect.y + cell_size // 2
        prev_center_x = center_x - incoming.x * cell_size
        prev_center_y = center_y - incoming.y * cell_size
        draw_x = prev_center_x + (center_x - prev_center_x) * self.item_progress
        draw_y = prev_center_y + (center_y - prev_center_y) * self.item_progress

        size = int(cell_size * 0.5)
        sprite = py.transform.scale(self.item.sprite, (size, size))
        screen.blit(sprite, (draw_x - camera.x - size // 2, draw_y - camera.y - size // 2))

    def refund_item_on_segment(self, player_inventory): # ok
        if self.item:
            player_inventory.try_add_items(self.item.item_id, 1)
            self._clear_item()

    def _clear_item(self): # ok
        self.item = None
        self.item_progress = 0.0

    def _pull_from_prev_machine(self, machines, cell_size):
        prev_rect = self.rect.move(-int(self.direction.x * cell_size), -int(self.direction.y * cell_size))
        for machine in machines:
            if isinstance(machine, ProducingMachine) and machine.rect.colliderect(prev_rect):
                # Peek at the next available output item
                next_item = machine.push_output_items(peek=True)
                if next_item:
                    # Actually remove the item from the machine
                    self.item = machine.push_output_items(peek=False)
                    self.item_progress = 0.0
                    self.incoming_direction = self.direction
                break  # Only pull from the first matching machine

    def _try_insert_into_machine(self, machine):
        if isinstance(machine, Splitter): # ok
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