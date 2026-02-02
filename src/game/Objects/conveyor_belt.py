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
        if not self.item or self.item.image is None: return

        if prev_direction is None: prev_direction = self.direction
        start_x = self.rect.x + cell_size // 2 - prev_direction.x * (cell_size // 2) ; start_y = self.rect.y + cell_size // 2 - prev_direction.y * (cell_size // 2)
        if prev_direction == self.direction:
            move_x = self.direction.x * cell_size * self.item_progress ; move_y = self.direction.y * cell_size * self.item_progress
        else:
            if self.item_progress < 0.5: t = self.item_progress / 0.5 ; move_x = prev_direction.x * (cell_size / 2) * t ; move_y = prev_direction.y * (cell_size / 2) * t
            else: t = (self.item_progress - 0.5) / 0.5 ; move_x = prev_direction.x * (cell_size / 2) + self.direction.x * (cell_size / 2) * t ; move_y = prev_direction.y * (cell_size / 2) + self.direction.y * (cell_size / 2) * t

        draw_x = start_x + move_x ; draw_y = start_y + move_y

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

    @classmethod
    def draw_ghost_belt(cls, screen, camera, x, y, direction: Vector2, color_flag="normal"):
        image = cls.get_image(direction).copy()
        image = py.transform.scale(image, (Grid.CELL_SIZE, Grid.CELL_SIZE))
        if color_flag == "normal":
            image.set_alpha(160)
            screen.blit(image, (x - camera.x, y - camera.y))
            return
        
        overlay = py.Surface((Grid.CELL_SIZE, Grid.CELL_SIZE), py.SRCALPHA)
        if color_flag == "red": overlay.fill((255, 0, 0, 120))
        elif color_flag == "orange": overlay.fill((255, 165, 0, 120))
        elif color_flag == "yellow": overlay.fill((255, 255, 0, 120))

        screen.blit(image, (x - camera.x, y - camera.y))
        screen.blit(overlay, (x - camera.x, y - camera.y))
    @classmethod
    def draw_ghost_belt_while_dragging(cls, screen, camera, rects, start_direction=None, color_flags=None):
        cell = Grid.CELL_SIZE
        image_cache = {}

        for i, rect in enumerate(rects):
            if i < len(rects) - 1: dx, dy = rects[i + 1].x - rect.x, rects[i + 1].y - rect.y
            elif i == 0 and start_direction: dx, dy = start_direction.x, start_direction.y
            else: dx, dy = rect.x - rects[i - 1].x, rect.y - rects[i - 1].y

            direction = Vector2(dx, dy).normalize() if dx or dy else Vector2(1, 0)
            key = (round(direction.x), round(direction.y))
            if key not in image_cache:
                img = py.transform.scale(cls.get_image(direction).copy(), (cell, cell))
                image_cache[key] = img
            belt_image = image_cache[key].copy()

            if color_flags:
                flag = color_flags[i]
                if flag == "normal":
                    belt_image.set_alpha(160)
                    screen.blit(belt_image, (rect.x - camera.x, rect.y - camera.y))
                    continue
                else:
                    overlay = py.Surface((cell, cell), py.SRCALPHA)
                    color_map = {"red": (255, 0, 0, 120), "orange": (255, 165, 0, 120), "yellow": (255, 255, 0, 120)}
                    overlay.fill(color_map.get(flag, (0, 0, 0, 0)))
                    screen.blit(belt_image, (rect.x - camera.x, rect.y - camera.y))
                    screen.blit(overlay, (rect.x - camera.x, rect.y - camera.y))
            else:
                screen.blit(belt_image, (rect.x - camera.x, rect.y - camera.y))
    @classmethod
    def get_image(cls, direction: Vector2):
        if direction.x > 0: key, path = "right", cls.SPRITE_PATH_RIGHT
        elif direction.x < 0: key, path = "left", cls.SPRITE_PATH_LEFT
        elif direction.y > 0: key, path = "down", cls.SPRITE_PATH_DOWN
        else: key, path = "up", cls.SPRITE_PATH_UP

        if key not in cls.IMAGES: cls.IMAGES[key] = py.image.load(path).convert_alpha()
        return cls.IMAGES[key]