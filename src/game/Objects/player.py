import pygame as py
from entities.inventory import Inventory
from core.vector2 import Vector2

class Player:
    def __init__(self, size, color = ("#6D366A")):
        self.inventory = Inventory(5, 9)

        self.color = color
        self.image = py.Surface((size, size)) ; self.image.fill(color)
        self.rect = self.image.get_rect() ; self.rect.x = 0 ; self.rect.y = 0
        self.speed = 7
        self.friction = 0.85

        self.dx = 0 ; self.dy = 0

    def update(self, machines):
        dx, dy = self.get_movement()

        self.rect.x += dx
        self.handle_collision_x(machines, dx)
        self.rect.y += dy
        self.handle_collision_y(machines, dy)

    def handle_collision_x(self, machines, dx):
        for machine in machines:
            if self.rect.colliderect(machine.rect):
                if dx > 0:  # moving right
                    self.rect.right = machine.rect.left
                elif dx < 0:  # moving left
                    self.rect.left = machine.rect.right
    def handle_collision_y(self, machines, dy):
        for machine in machines:
            if self.rect.colliderect(machine.rect):
                if dy > 0:  # moving down
                    self.rect.bottom = machine.rect.top
                elif dy < 0:  # moving up
                    self.rect.top = machine.rect.bottom

    def get_movement(self):
        keys = py.key.get_pressed()

        right = keys[py.K_RIGHT] or keys[py.K_d]
        left = keys[py.K_LEFT] or keys[py.K_a]
        down = keys[py.K_DOWN] or keys[py.K_s]
        up = keys[py.K_UP] or keys[py.K_w]

        moving_x = right - left
        moving_y = down - up

        multiplier = self.speed * (1-self.friction) / self.friction
        movement = Vector2(moving_x, moving_y).normalize() * multiplier

        #dx, dy = 0, 0

        self.dx += movement.x
        self.dy += movement.y
        self.dx *= self.friction
        self.dy *= self.friction

        return self.dx, self.dy

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))