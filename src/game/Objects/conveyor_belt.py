import pygame as py
from grid.grid import Grid
from core.vector2 import Vector2

import pygame as py
from grid.grid import Grid
from core.vector2 import Vector2

class BeltSegment:
    def __init__(self, rect: py.Rect, direction: Vector2, items_per_minute=60):
        self.rect = rect
        self.direction = direction  # must be integer Vector2 (1,0), (0,1), etc.)
        self.item = None
        self.item_progress = 0.0
        self.BUILD_COST = {"iron_ingot": 2}

        self.items_per_minute = items_per_minute
        self.speed = (self.items_per_minute / 60) * Grid.CELL_SIZE

    def update(self, all_segments, machines, cell_size, dt):
        # move item along this segment
        if self.item:
            self.item_progress += self.speed * dt / cell_size
            if self.item_progress >= 1.0:
                # try to move to next segment
                next_rect = self.rect.move(int(self.direction.x * cell_size), int(self.direction.y * cell_size))
                moved = False
                for segment in all_segments:
                    if segment.rect.topleft == next_rect.topleft and segment.item is None:
                        segment.item = self.item
                        segment.item_progress = 0.0  # start at beginning
                        self.item = None
                        moved = True
                        break

                # If no next segment, try to push into machine
                if not moved:
                    for machine in machines:
                        if machine.rect.colliderect(next_rect):
                            if self.item.item_id in machine.recipe.inputs:
                                added = machine.input_inventory.add_items(self.item, 1)
                                if added:
                                    self.item = None
                            break

                # cap progress if blocked
                if self.item:
                    self.item_progress = 1.0

        # pull from machine if belt is empty
        if self.item is None:
            prev_rect = self.rect.move(-int(self.direction.x * cell_size), -int(self.direction.y * cell_size))
            for machine in machines:
                if machine.rect.colliderect(prev_rect):
                    item = machine.push_output_item(peek=True)
                    if item:
                        self.item = machine.push_output_item()  # actually take it
                        self.item_progress = 0.0
                        break

    def draw_item(self, screen, camera, cell_size, prev_direction=None):
        if not self.item or self.item.image is None:
            return

        # If no previous direction, assume straight
        if prev_direction is None:
            prev_direction = self.direction

        # Start at incoming edge (opposite of prev_direction)
        start_x = self.rect.x + cell_size // 2 - prev_direction.x * (cell_size // 2)
        start_y = self.rect.y + cell_size // 2 - prev_direction.y * (cell_size // 2)

        # Check if corner
        if prev_direction == self.direction:
            # Straight belt
            move_x = self.direction.x * cell_size * self.item_progress
            move_y = self.direction.y * cell_size * self.item_progress
        else:
            # Corner: two-phase movement
            if self.item_progress < 0.5:
                t = self.item_progress / 0.5  # 0 -> 1 in first half
                move_x = prev_direction.x * (cell_size / 2) * t
                move_y = prev_direction.y * (cell_size / 2) * t
            else:
                t = (self.item_progress - 0.5) / 0.5  # 0 -> 1 in second half
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
    IMAGES = {}  # cache loaded images

    def __init__(self, rects: list):
        self.segments = []

        for i in range(len(rects)):
            rect = rects[i]

            # determine direction to next/prev segment
            if i < len(rects) - 1:
                next_rect = rects[i + 1]
                dx = next_rect.x - rect.x
                dy = next_rect.y - rect.y
            elif i > 0:
                prev_rect = rects[i - 1]
                dx = rect.x - prev_rect.x
                dy = rect.y - prev_rect.y
            else:
                dx, dy = Grid.CELL_SIZE, 0  # default right

            # convert to integer grid direction
            if dx > 0: direction = Vector2(1, 0)
            elif dx < 0: direction = Vector2(-1, 0)
            elif dy > 0: direction = Vector2(0, 1)
            elif dy < 0: direction = Vector2(0, -1)
            else: direction = Vector2(1, 0)

            self.segments.append(BeltSegment(rect, direction))

    def draw(self, screen, camera, all_belts):
        cell = Grid.CELL_SIZE
        all_segments = [s for b in all_belts for s in b.segments]

        for seg in self.segments:
            # Draw belt tile
            image = py.transform.scale(self.get_image(seg.direction), (cell, cell))
            screen.blit(image, (seg.rect.x - camera.x, seg.rect.y - camera.y))

            # Find previous segment (for corner calculation)
            prev_seg = None
            for s in all_segments:
                if s.rect.x + s.direction.x * cell == seg.rect.x and s.rect.y + s.direction.y * cell == seg.rect.y:
                    prev_seg = s
                    break

            seg.draw_item(screen, camera, cell_size=cell, prev_direction=prev_seg.direction if prev_seg else seg.direction)



    @classmethod
    def draw_ghost_belt(cls, screen, camera, x, y, direction: Vector2, color_flag="normal"):
        image = cls.get_image(direction).copy()
        image = py.transform.scale(image, (Grid.CELL_SIZE, Grid.CELL_SIZE))
        
        overlay = py.Surface((Grid.CELL_SIZE, Grid.CELL_SIZE), py.SRCALPHA)
        
        if color_flag == "red":
            overlay.fill((255, 0, 0, 120))
        elif color_flag == "orange":
            overlay.fill((255, 165, 0, 120))
        elif color_flag == "normal":
            overlay.fill((200, 200, 200, 100))  # ✨ subtle gray alpha for normal
        
        screen.blit(image, (x - camera.x, y - camera.y))
        screen.blit(overlay, (x - camera.x, y - camera.y))


    @classmethod
    def draw_ghost_belt_while_dragging(cls, screen, camera, rects, start_direction=None, color_flags=None):
        cell = Grid.CELL_SIZE ; image_cache = {}
        for i, rect in enumerate(rects):
            if i < len(rects)-1: dx, dy = rects[i+1].x - rect.x, rects[i+1].y - rect.y
            elif i == 0 and start_direction: dx, dy = start_direction.x, start_direction.y
            else: dx, dy = rect.x - rects[i-1].x, rect.y - rects[i-1].y
            direction = Vector2(dx, dy).normalize() if dx or dy else Vector2(1,0)
            key = (round(direction.x), round(direction.y))
            if key not in image_cache: img = py.transform.scale(cls.get_image(direction).copy(), (cell, cell)) ; image_cache[key] = img
            screen.blit(image_cache[key], (rect.x - camera.x, rect.y - camera.y))
            if color_flags:
                overlay = py.Surface((cell, cell), py.SRCALPHA)
                color_map = {
                    "red": (255,0,0,120),
                    "orange": (255,165,0,120),
                    "yellow": (255,255,0,120),
                    "normal": (200, 200, 200, 100)  # ✨ add alpha overlay for normal
                }
                overlay.fill(color_map[color_flags[i]])
                screen.blit(overlay, (rect.x - camera.x, rect.y - camera.y))


    @classmethod
    def get_image(cls, direction: Vector2):
        if direction.x > 0: key, path = "right", cls.SPRITE_PATH_RIGHT
        elif direction.x < 0: key, path = "left", cls.SPRITE_PATH_LEFT
        elif direction.y > 0: key, path = "down", cls.SPRITE_PATH_DOWN
        else: key, path = "up", cls.SPRITE_PATH_UP

        if key not in cls.IMAGES:
            cls.IMAGES[key] = py.image.load(path).convert_alpha()
        return cls.IMAGES[key]