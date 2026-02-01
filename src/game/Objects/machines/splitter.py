import pygame as py
from core.vector2 import Vector2

class Splitter:
    SIZE = 32
    SPRITE_PATH = "assets/Sprites/machines/splitter.png"
    BUILD_COST = {"iron_ingot": 4}

    def __init__(self, pos=None, direction=None):
        self.rect = py.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = pos

        self.direction = direction or Vector2(1, 0)
        self.current_item = None
        self.current_output_index = 0
        self.output_belts = []

        # For drawing
        self.image_original = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            self.image_original.blit(py.transform.scale(original, (self.SIZE, self.SIZE)), (0, 0))
        self.image = self.image_original.copy()
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

            if seg and seg.item is None and seg.direction == direction:
                seg.item = self.current_item
                self.current_item = None
                self.current_output_index = (self.current_output_index + 1) % num_dirs
                return True

            self.current_output_index = (self.current_output_index + 1) % num_dirs

        return False

    def _get_relative_dirs(self):
        dx, dy = float(self.direction.x), float(self.direction.y)
        return [Vector2(-dy, dx), Vector2(dx, dy), Vector2(dy, -dx)]

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

    @classmethod
    def draw_ghost_machine(cls, screen, camera, pos, blocked, player_inventory):
        ghost = py.Surface((cls.SIZE, cls.SIZE), py.SRCALPHA)
        if cls.SPRITE_PATH:
            original = py.image.load(cls.SPRITE_PATH).convert_alpha()
            img = py.transform.scale(original, (cls.SIZE, cls.SIZE))
            ghost.blit(img, (0, 0))
        ghost.set_alpha(120)
        cannot_afford = False
        if player_inventory is not None:
            cannot_afford = not player_inventory.has_enough_build_cost_items(cls.BUILD_COST)
        if blocked or cannot_afford:
            ghost.fill((255, 0, 0, 80), special_flags=py.BLEND_RGBA_MULT)
        screen.blit(ghost, (pos[0] - camera.x - cls.SIZE // 2, pos[1] - camera.y - cls.SIZE // 2))