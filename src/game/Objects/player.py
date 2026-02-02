import pygame as py
from entities.inventory import Inventory
from core.vector2 import Vector2

class Player:
    def __init__(self, size, color = ("#5F2D5D")):
        self.inventory = Inventory(5, 9)

        self.color = color
        self.image = py.Surface((size, size)) ; self.image.fill(color)
        self.rect = self.image.get_rect() ; self.rect.centerx=0 ; self.rect.centery=0
        self.speed = 1.5
        self.friction = 0.85

        self.dx = 0 ; self.dy = 0

    def update(self, machines):
        dx, dy = self.get_movement()

        if dx:
            self.rect.x += dx
            self.handle_collision_x(machines, dx)

        if dy:
            self.rect.y += dy
            self.handle_collision_y(machines, dy)


    def handle_collision_x(self, machines, dx):
        for machine in machines:
            if abs(machine.rect.centerx - self.rect.centerx) > 64:
                continue
            if self.rect.colliderect(machine.rect):
                if dx > 0:
                    self.rect.right = machine.rect.left
                elif dx < 0:
                    self.rect.left = machine.rect.right

    def handle_collision_y(self, machines, dy):
        for machine in machines:
            if abs(machine.rect.centery - self.rect.centery) > 64:
                continue
            if self.rect.colliderect(machine.rect):
                if dy > 0:
                    self.rect.bottom = machine.rect.top
                elif dy < 0:
                    self.rect.top = machine.rect.bottom



    def get_movement(self):
        keys = py.key.get_pressed()

        # Determine movement directions
        moving_x = (keys[py.K_RIGHT] or keys[py.K_d]) - (keys[py.K_LEFT] or keys[py.K_a])
        moving_y = (keys[py.K_DOWN]  or keys[py.K_s]) - (keys[py.K_UP]   or keys[py.K_w])

        # Normalize diagonal movement
        if moving_x != 0 and moving_y != 0:
            factor = 0.7071  # 1/sqrt(2)
        else:
            factor = 1.0

        # Apply speed and friction
        self.dx += moving_x * self.speed * factor
        self.dy += moving_y * self.speed * factor

        self.dx *= self.friction
        self.dy *= self.friction

        return self.dx, self.dy




    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))