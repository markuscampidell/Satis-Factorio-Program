# entities.item
import pygame as py
import os

class Item:
    def __init__(self, item_id:str, name:str, stack_size=100, sprite_path=None):
        self.item_id = item_id
        self.name = name
        self.stack_size = stack_size
        self.sprite_path = sprite_path
        self.sprite = None
        self._scaled_sprite_cache = {}

    def load_sprite(self):
        if self.sprite_path and os.path.isfile(self.sprite_path):
            self.sprite = py.image.load(self.sprite_path).convert_alpha()

    def get_scaled_sprite(self, size):
        # Cache scaled sprites by size to avoid repeating expensive transforms.
        if size in self._scaled_sprite_cache:
            return self._scaled_sprite_cache[size]
        if not self.sprite:
            return None
        scaled = py.transform.scale(self.sprite, (size, size))
        self._scaled_sprite_cache[size] = scaled
        return scaled