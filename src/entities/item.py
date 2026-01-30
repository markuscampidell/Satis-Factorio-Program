import pygame as py

import pygame as py
import os

class Item:
    def __init__(self, item_id, name, stack_size=100, sprite_path=None):
        self.item_id = item_id
        self.name = name
        self.stack_size = stack_size
        self.sprite_path = sprite_path
        self.image = None  # only one sprite

    def load_sprite(self):
        if self.sprite_path and os.path.isfile(self.sprite_path):
            self.image = py.image.load(self.sprite_path).convert_alpha()
        else:
            pass
            #print(f"Sprite not found for item {self.item_id}: {self.sprite_path}")
