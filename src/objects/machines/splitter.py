# objects.machines.splitter
import pygame as py
from pygame.transform import rotate

from core.vector2 import Vector2
from objects.machines.machine import Machine
from objects.machines.producing_machine import ProducingMachine
from game.grid import Grid

class Splitter(Machine):
    WIDTH = 1
    HEIGHT = 1
    SPRITE_PATH = "src/assets/sprites/machines/splitter.png"
    BUILD_COST = {"iron_ingot": 4}

    DEFAULT_TILES_PER_SEC = 2.0

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
        self.item_progress = 0.0
        self.current_item_speed = self.DEFAULT_TILES_PER_SEC

    def update(self, dt, belt_map, machine_map=None):
        if not self.current_item:
            self.item_progress = 0.0
            return

        self.item_progress += self.current_item_speed * dt

        if self.item_progress >= 1.0:
            moved = self.push_item(belt_map, machine_map)
            if moved:
                self.item_progress = 0.0
            else:
                self.item_progress = 1.0

    def push_item(self, belt_map, machine_map=None):
        if not self.current_item:
            return False

        machine_map = machine_map or {}
        relative_dirs = self._get_relative_dirs()
        num_dirs = len(relative_dirs)

        for _ in range(num_dirs):
            direction = relative_dirs[self.current_output_index % num_dirs]
            next_tile = (self.grid_pos[0] + int(direction.x), self.grid_pos[1] + int(direction.y))
            seg = belt_map.get(next_tile)

            if seg is not None:
                if seg.item is None and direction != -seg.direction:
                    seg.item = self.current_item
                    seg.item_progress = 0.0

                    # The item enters this belt from the splitter direction
                    seg.current_incoming_direction = direction

                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True
            else:
                machine = machine_map.get(next_tile)

                accepted = False
                if isinstance(machine, ProducingMachine):
                    accepted = machine.try_receive_item(self.current_item, self.grid_pos, self.current_item_speed)
                elif isinstance(machine, Splitter):
                    accepted = machine.receive_item(self.current_item, incoming_direction=direction, source_speed=self.current_item_speed)

                if accepted:
                    self.current_item = None
                    self.current_output_index = (self.current_output_index + 1) % num_dirs
                    return True

            self.current_output_index = (self.current_output_index + 1) % num_dirs

        return False

    def _get_relative_dirs(self):
        dx, dy = float(self.direction.x), float(self.direction.y)
        return [
            Vector2(-dy, dx),  # left
            Vector2(dx, dy),   # forward
            Vector2(dy, -dx),  # right
        ]

    def receive_item(self, item, incoming_direction: Vector2 = None, source_speed=None):
        if self.current_item is not None:
            return False

        if incoming_direction != self.direction:
            return False

        self.current_item = item
        self.current_incoming_direction = incoming_direction
        self.item_progress = 0.0
        self.current_item_speed = source_speed if source_speed is not None else self.DEFAULT_TILES_PER_SEC

        return True

    def get_refund_items(self):
        refund = super().get_refund_items()
        if self.current_item:
            item_id = self.current_item.item_id if hasattr(self.current_item, "item_id") else self.current_item
            refund[item_id] = refund.get(item_id, 0) + 1
        return refund

    def rotate(self):
        self.direction = Vector2(-self.direction.y, self.direction.x)
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.image = rotate(self.image_original, -self.rotation_angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect(center=old_center)

    def draw(self, screen, camera):
        draw_x = self.grid_pos[0] * self.cell_size - camera.x
        draw_y = self.grid_pos[1] * self.cell_size - camera.y
        screen.blit(self.image, (draw_x, draw_y))