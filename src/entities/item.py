import pygame as py

class Item:
    def __init__(self, item_id, name, stack_size=100, sprite_path=None):
        self.item_id = item_id
        self.name = name
        self.stack_size = stack_size
        self.sprite_path = sprite_path
        self.image = None  # don't load yet

    def load_sprite(self):
        if self.sprite_path and self.image is None:
            self.image = py.image.load(self.sprite_path).convert_alpha()