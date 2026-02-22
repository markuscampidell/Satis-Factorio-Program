import pygame as py
from core.vector2 import Vector2
from objects.machines.machine import Machine

class Splitter(Machine):
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = "src/assets/sprites/machines/splitter.png"
    BUILD_COST = {"iron_ingot": 4}

    def __init__(self, pos=None, direction=None):
        super().__init__(pos)  # creates rect & image correctly

        self.direction = direction or Vector2(1, 0)
        self.current_item = None
        self.current_output_index = 0
        self.output_belts = []

        self.image_original = self.image.copy()  # keep original for rotation
        self.rotation_angle = 0

        self.item_progress = 0.0
        self.ITEMS_PER_MINUTE = 120
        self.speed = self.ITEMS_PER_MINUTE / 60

    def update(self, dt, cell_size, belt_map):
        if not self.current_item:
            self.item_progress = 0.0
            return
        
        self.item_progress += self.speed * dt

        if self.item_progress >= 1.0:
            moved = self.push_item(cell_size, belt_map)
            if moved: self.item_progress = 0.0
            else: self.item_progress = 1.0

    def update_outputs(self, belt_map, cell_size):
        belts = []
        for direction in self._get_relative_dirs():
            next_rect = self.rect.move(int(direction.x * cell_size), int(direction.y * cell_size))
            seg = belt_map.get((next_rect.x, next_rect.y))
            if seg: belts.append(seg)
        self.output_belts = belts
        if self.current_output_index >= len(self.output_belts):
            self.current_output_index = 0

    def push_item(self, cell_size, belt_map):
        if not self.current_item: return False

        relative_dirs = self._get_relative_dirs()
        num_dirs = len(relative_dirs)

        for _ in range(num_dirs):
            direction = relative_dirs[self.current_output_index % num_dirs]
            next_rect = self.rect.move(int(direction.x * cell_size), int(direction.y * cell_size))
            seg = belt_map.get((next_rect.x, next_rect.y))

            if seg and seg.item is None:
                # For straight belts, check the direction. For curves, check incoming_direction
                if seg.incoming_direction and seg.direction != seg.incoming_direction:
                    # Curve: check if incoming_direction matches the push direction
                    acceptable = seg.incoming_direction == direction
                else:
                    # Straight belt: check if direction matches the push direction
                    acceptable = seg.direction == direction
                
                if acceptable:
                    seg.item = self.current_item
                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True

            self.current_output_index = (self.current_output_index + 1) % num_dirs

        return False

    def _get_relative_dirs(self):
        dx, dy = float(self.direction.x), float(self.direction.y)
        return [Vector2(-dy, dx), 
                Vector2(dx, dy), 
                Vector2(dy, -dx)]

    def receive_item(self, item, incoming_direction: Vector2 = None):
        if self.current_item is not None: return False
        if incoming_direction and incoming_direction != self.direction: return False
        self.current_item = item
        return True

    def rotate(self):
        self.direction = Vector2(-self.direction.y, self.direction.x)
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.image = py.transform.rotate(self.image_original, -self.rotation_angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect(center=old_center)

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))