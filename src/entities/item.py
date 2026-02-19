import pygame as py
import os

class Item:
    """
    Example:
    
    Item = {item_id = "my_item",
            name = "My Item",
            stack_size = 100,
            sprite_path = "assets/items/my_item.png"}
    """
    def __init__(self, item_id, name, stack_size=100, sprite_path=None):
        self.item_id = item_id
        self.name = name
        self.stack_size = stack_size
        self.sprite_path = sprite_path
        self.sprite = None

    def load_sprite(self):
        if self.sprite_path and os.path.isfile(self.sprite_path):
            self.sprite = py.image.load(self.sprite_path).convert_alpha()