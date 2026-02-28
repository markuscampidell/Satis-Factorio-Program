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

    def load_sprite(self):
        if self.sprite_path and os.path.isfile(self.sprite_path):
            self.sprite = py.image.load(self.sprite_path).convert_alpha()