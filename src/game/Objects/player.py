import pygame as py
from math import sqrt
from entities.inventory import Inventory

class Player:
    def __init__(self, size, color = ("#534BBE")):
        self.inventory = Inventory()

        self.color = color
        self.image = py.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.speed = 5

    def update(self, smelters):
        dx, dy = self.get_movement()

        self.rect.x += dx
        self.handle_collision_x(smelters, dx)
        self.rect.y += dy
        self.handle_collision_y(smelters, dy)

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

        moving_x = right or left
        moving_y = down or up

        if moving_x and moving_y: new_speed = self.speed / sqrt(2)
        else: new_speed = self.speed

        dx, dy = 0, 0

        if right: dx += new_speed
        if left: dx -= new_speed
        if down: dy += new_speed
        if up: dy -= new_speed

        return dx, dy

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))