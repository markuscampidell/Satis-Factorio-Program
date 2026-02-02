import pygame as py

from grid.grid import Grid
from core.vector2 import Vector2
from game.Objects.conveyor_belt import ConveyorBelt

def draw_ghost_belt(screen, camera, x, y, direction: Vector2, color_flag="normal"):
    image = get_image(ConveyorBelt, direction).copy()
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

def draw_ghost_belt_while_dragging(screen, camera, rects, start_direction=None, color_flags=None):
    cell = Grid.CELL_SIZE
    image_cache = {}

    for i, rect in enumerate(rects):
        if i < len(rects) - 1: dx, dy = rects[i + 1].x - rect.x, rects[i + 1].y - rect.y
        elif i == 0 and start_direction: dx, dy = start_direction.x, start_direction.y
        else: dx, dy = rect.x - rects[i - 1].x, rect.y - rects[i - 1].y

        direction = Vector2(dx, dy).normalize() if dx or dy else Vector2(1, 0)
        key = (round(direction.x), round(direction.y))
        if key not in image_cache:
            img = py.transform.scale(get_image(ConveyorBelt, direction).copy(), (cell, cell))
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

def get_image(cls, direction: Vector2):
    if direction.x > 0: key, path = "right", cls.SPRITE_PATH_RIGHT
    elif direction.x < 0: key, path = "left", cls.SPRITE_PATH_LEFT
    elif direction.y > 0: key, path = "down", cls.SPRITE_PATH_DOWN
    else: key, path = "up", cls.SPRITE_PATH_UP

    if key not in cls.IMAGES: cls.IMAGES[key] = py.image.load(path).convert_alpha()
    return cls.IMAGES[key]