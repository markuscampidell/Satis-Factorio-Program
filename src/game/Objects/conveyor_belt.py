import pygame as py
from grid.grid import Grid
from core.vector2 import Vector2
from constants.itemdata import get_item_by_id
from game.Objects.machines.producing_machine import ProducingMachine
from game.Objects.machines.splitter import Splitter

class BeltSegment:
    def __init__(self, rect: py.Rect, direction: Vector2, items_per_minute=120):
        self.rect = rect
        self.direction = direction
        self.item = None
        self.item_progress = 0.0
        self.BUILD_COST = {"iron_ingot": 2}

        self.items_per_minute = items_per_minute
        self.speed = (self.items_per_minute / 60) * Grid.CELL_SIZE

    def update(self, belt_map, machines, cell_size, dt):
        if self.item: 
            self.item_progress += self.speed * dt / cell_size

            if self.item_progress >= 1.0:
                next_rect = self.rect.move(int(self.direction.x * cell_size), int(self.direction.y * cell_size))
                moved = False
                next_segment = belt_map.get(next_rect.topleft)
                if next_segment and next_segment.item is None:
                    next_segment.item = self.item
                    next_segment.item_progress = 0.0
                    self.item = None
                    moved = True

                if not moved:
                    for machine in machines:
                        if machine.rect.colliderect(next_rect):
                            if isinstance(machine, Splitter):
                                success = machine.receive_item(self.item, incoming_direction=self.direction)
                                if success:
                                    self.item = None
                                    moved = True

                            elif isinstance(machine, ProducingMachine):
                                for inv_item_id, inv in machine.input_inventories.items():
                                    if self.item.item_id == inv_item_id:
                                        added = inv.add_items(self.item, 1)
                                        if added:
                                            self.item = None
                                            moved = True
                                        break
                            break

                if self.item: self.item_progress = 1.0
                else: self.item_progress = 0.0

        if self.item is None:
            prev_rect = self.rect.move(-int(self.direction.x * cell_size), -int(self.direction.y * cell_size))
            for machine in machines:
                if machine.rect.colliderect(prev_rect):
                    if isinstance(machine, ProducingMachine):
                        item_obj = machine.push_output_item(peek=True)
                        if item_obj:
                            self.item = machine.push_output_item(peek=False)
                            self.item_progress = 0.0
                    break

    def refund_item(self, player_inventory):
        if self.item:
            if player_inventory: player_inventory.add_items(self.item, 1)
            self.item = None
            self.item_progress = 0.0

    def draw_item(self, screen, camera, cell_size, prev_direction=None):
        if not self.item or self.item.image is None:
            return

        if prev_direction is None:
            prev_direction = self.direction

        start_x = self.rect.x + cell_size // 2
        start_y = self.rect.y + cell_size // 2

        if prev_direction == self.direction:
            move_x = self.direction.x * cell_size * self.item_progress
            move_y = self.direction.y * cell_size * self.item_progress
        else:
            if self.item_progress < 0.5:
                t = self.item_progress / 0.5
                move_x = prev_direction.x * (cell_size / 2) * t
                move_y = prev_direction.y * (cell_size / 2) * t
            else:
                t = (self.item_progress - 0.5) / 0.5
                move_x = prev_direction.x * (cell_size / 2) + self.direction.x * (cell_size / 2) * t
                move_y = prev_direction.y * (cell_size / 2) + self.direction.y * (cell_size / 2) * t

        draw_x = start_x + move_x
        draw_y = start_y + move_y

        size = int(cell_size * 0.5)
        sprite = py.transform.scale(self.item.image, (size, size))
        screen.blit(sprite, (draw_x - camera.x - size // 2, draw_y - camera.y - size // 2))



class ConveyorBelt:
    SPRITE_PATH_RIGHT = "assets/Sprites/conveyors/belt_right.png"
    SPRITE_PATH_LEFT  = "assets/Sprites/conveyors/belt_left.png"
    SPRITE_PATH_UP    = "assets/Sprites/conveyors/belt_up.png"
    SPRITE_PATH_DOWN  = "assets/Sprites/conveyors/belt_down.png"
    IMAGES = {}

    def __init__(self, rects: list):
        self.segments = []
        for i in range(len(rects)):
            rect = rects[i]

            if i < len(rects) - 1:
                next_rect = rects[i + 1]
                dx = next_rect.x - rect.x
                dy = next_rect.y - rect.y
            elif i > 0:
                prev_rect = rects[i - 1]
                dx = rect.x - prev_rect.x
                dy = rect.y - prev_rect.y
            else:
                dx, dy = Grid.CELL_SIZE, 0

            if dx > 0: direction = Vector2(1, 0)
            elif dx < 0: direction = Vector2(-1, 0)
            elif dy > 0: direction = Vector2(0, 1)
            elif dy < 0: direction = Vector2(0, -1)
            else: direction = Vector2(1, 0)

            self.segments.append(BeltSegment(rect, direction))
    
    def refund_all_items(self, player_inventory):
        for segment in self.segments:
            segment.refund_item(player_inventory)

    def draw(self, screen, camera, belt_map):
        cell = Grid.CELL_SIZE
        for seg in self.segments:
            image = py.transform.scale(self.get_image(seg.direction), (cell, cell))
            screen.blit(image, (seg.rect.x - camera.x, seg.rect.y - camera.y))
            prev_pos = (seg.rect.x - seg.direction.x * cell, seg.rect.y - seg.direction.y * cell)
            prev_seg = belt_map.get(prev_pos)

            seg.draw_item(screen, camera, cell_size=cell, prev_direction=prev_seg.direction if prev_seg else seg.direction)
    