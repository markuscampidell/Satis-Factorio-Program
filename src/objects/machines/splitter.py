# objects.machines.splitter
import pygame as py
from pygame.transform import rotate

from core.vector2 import Vector2
from objects.machines.machine import Machine
from game.grid import Grid

class Splitter(Machine):
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = "src/assets/sprites/machines/splitter.png"
    BUILD_COST = {"iron_ingot": 4}

    def __init__(self, grid_pos=(0,0), direction=None, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)

        # TILE-BASED POSITION
        self.grid_pos = grid_pos  # (x, y) in tiles
        self.cell_size = cell_size

        # Rotation / direction
        self.direction = direction or Vector2(1, 0)
        self.rotation_angle = 0

        # Image
        self.image_original = self.image.copy()
        self.rect = py.Rect(
            self.grid_pos[0] * cell_size,
            self.grid_pos[1] * cell_size,
            self.WIDTH * cell_size,
            self.HEIGHT * cell_size
        )

        # Item handling
        self.current_item = None
        self.current_output_index = 0
        self.output_belts = []
        self.item_progress = 0.0
        self.ITEMS_PER_MINUTE = 120
        self.speed = self.ITEMS_PER_MINUTE / 60  # tiles per second

    # ------------------------
    # Update per frame
    # ------------------------
    def update(self, dt, belt_map):
        if not self.current_item:
            self.item_progress = 0.0
            return

        self.item_progress += self.speed * dt

        if self.item_progress >= 1.0:
            moved = self.push_item(belt_map)
            if moved:
                self.item_progress = 0.0
            else:
                self.item_progress = 1.0

    # ------------------------
    # Update output belts
    # ------------------------
    def update_outputs(self, belt_map):
        belts = []
        for direction in self._get_relative_dirs():
            next_tile = (self.grid_pos[0] + int(direction.x), self.grid_pos[1] + int(direction.y))
            seg = belt_map.get(next_tile)
            if seg:
                belts.append(seg)
        self.output_belts = belts
        if self.current_output_index >= len(self.output_belts):
            self.current_output_index = 0

    # ------------------------
    # Push item to one of the output belts
    # ------------------------
    def push_item(self, belt_map):
        if not self.current_item:
            return False

        relative_dirs = self._get_relative_dirs()
        num_dirs = len(relative_dirs)

        for _ in range(num_dirs):
            direction = relative_dirs[self.current_output_index % num_dirs]
            next_tile = (self.grid_pos[0] + int(direction.x), self.grid_pos[1] + int(direction.y))
            seg = belt_map.get(next_tile)

            if seg and seg.item is None:
                # Check if push direction matches belt segment
                if seg.incoming_direction and seg.direction != seg.incoming_direction:
                    acceptable = seg.incoming_direction == direction
                else:
                    acceptable = seg.direction == direction

                if acceptable:
                    seg.item = self.current_item
                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True

            self.current_output_index = (self.current_output_index + 1) % num_dirs

        return False

    # ------------------------
    # Return directions relative to current rotation
    # ------------------------
    def _get_relative_dirs(self):
        dx, dy = float(self.direction.x), float(self.direction.y)
        return [
            Vector2(-dy, dx),  # left
            Vector2(dx, dy),   # forward
            Vector2(dy, -dx),  # right
        ]

    # ------------------------
    # Receive item from upstream
    # ------------------------
    def receive_item(self, item, incoming_direction: Vector2 = None):
        if self.current_item is not None:
            return False
        if incoming_direction and incoming_direction != self.direction:
            return False
        self.current_item = item
        return True

    # ------------------------
    # Rotate the splitter
    # ------------------------
    def rotate(self):
        self.direction = Vector2(-self.direction.y, self.direction.x)
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.image = rotate(self.image_original, -self.rotation_angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect(center=old_center)

    # ------------------------
    # Draw splitter
    # ------------------------
    def draw(self, screen, camera):
        draw_x = self.grid_pos[0] * self.cell_size - camera.x
        draw_y = self.grid_pos[1] * self.cell_size - camera.y
        screen.blit(self.image, (draw_x, draw_y))