import pygame as py

class Machine:
    SIZE = 96
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, pos):
        self.rect = py.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = pos

        self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            self.image.blit(py.transform.scale(original, (self.SIZE, self.SIZE)), (0, 0))

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))

    @classmethod
    def draw_ghost_machine(cls, screen, camera, pos, blocked, player_inventory):
        if cls.SPRITE_PATH is None: return
        original = py.image.load(cls.SPRITE_PATH).convert_alpha()
        w, h = original.get_size()
        image = py.transform.scale(original, (w * 2, h * 2))
        ghost = py.Surface((cls.SIZE, cls.SIZE), py.SRCALPHA)
        ghost.blit(image, (0, 0))
        ghost.set_alpha(120)
        cannot_afford = False
        if player_inventory is not None: cannot_afford = not player_inventory.has_enough_build_cost_items(cls.BUILD_COST)
        if blocked or cannot_afford: ghost.fill((255, 0, 0, 80), special_flags=py.BLEND_RGBA_MULT)
        screen.blit(ghost, (pos[0] - camera.x - cls.SIZE // 2, pos[1] - camera.y - cls.SIZE // 2))