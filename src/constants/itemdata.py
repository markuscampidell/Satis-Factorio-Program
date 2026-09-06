# constants.itemdata

import pygame as py
import os

class Item:
    """One kind of item in the game, like iron ore or a copper ingot.
    This is just the item's info card - it doesn't track how many you
    have, Inventory does that."""

    def __init__(self, item_id:str, name:str, stack_size=100, sprite_path=None):
        self.item_id = item_id
        self.name = name
        self.stack_size = stack_size
        self.sprite_path = sprite_path
        self.sprite = None
        self._scaled_sprite_cache = {}

    def load_sprite(self):
        """Loads this item's picture from disk, if it has one."""
        if self.sprite_path and os.path.isfile(self.sprite_path):
            self.sprite = py.image.load(self.sprite_path).convert_alpha()

    def get_scaled_sprite(self, size):
        """Gives back this item's picture resized to `size`. Remembers
        sizes it already made, so it doesn't redo the resizing every time."""
        if size in self._scaled_sprite_cache:
            return self._scaled_sprite_cache[size]
        if not self.sprite:
            return None
        scaled = py.transform.scale(self.sprite, (size, size))
        self._scaled_sprite_cache[size] = scaled
        return scaled


raw_materials = []
limestone = Item("limestone", "Limestone")
iron_ore = Item("iron_ore", "Iron Ore", sprite_path = "src/assets/sprites/items/raw_materials/iron_ore.png")
copper_ore = Item("copper_ore", "Copper Ore", sprite_path = "src/assets/sprites/items/raw_materials/copper_ore.png")
coal = Item("coal", "Coal", sprite_path = "src/assets/sprites/items/raw_materials/coal.png")
raw_materials.extend([limestone, iron_ore, copper_ore, coal])


ingots = []
iron_ingot = Item("iron_ingot", "Iron Ingot", sprite_path = "src/assets/sprites/items/ingots/iron_ingot.png")
copper_ingot = Item("copper_ingot", "Copper Ingot", sprite_path = "src/assets/sprites/items/ingots/copper_ingot.png")
steel = Item("steel", "Steel", sprite_path="src/assets/sprites/items/ingots/steel.png")
ingots.extend([iron_ingot, copper_ingot, steel])


minerals = []
concrete = Item("concrete", "Concrete", sprite_path="src/assets/sprites/items/minerals/concrete.png")
minerals.extend([concrete])


standard_parts = []
iron_plate = Item("iron_plate", "Iron Plate", sprite_path="src/assets/sprites/items/standard_parts/iron_plate.png")
iron_rod = Item("iron_rod", "Iron Rod", sprite_path="src/assets/sprites/items/standard_parts/iron_rod.png")
standard_parts.extend([iron_plate, iron_rod])



ITEMS = [raw_materials, ingots, minerals, standard_parts]
ITEMS = [item for category in ITEMS for item in category]



def get_item_by_id(item_id):
    for item in ITEMS:
        if item.item_id == item_id:
            return item
    return None