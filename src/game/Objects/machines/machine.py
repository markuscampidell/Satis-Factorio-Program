import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory
from core.vector2 import Vector2

import pygame as py
from constants.itemdata import get_item_by_id

class Machine:
    SIZE = 96
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, pos, recipe=None):
        self.recipe = recipe
        self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            image = py.transform.scale(original, (self.SIZE, self.SIZE))
            self.image.blit(image, (0, 0))
        self.rect = self.image.get_rect(center=pos)

        input_slots = len(recipe.inputs)
        self.input_inventory = Inventory(slot_width=input_slots, slot_height=1)


        self.output_inventory = Inventory(slot_width=1, slot_height=1)

        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

    def get_recipe_input(self):
        if not self.recipe or not self.recipe.inputs:
            return None, 0
        return next(iter(self.recipe.inputs.items()))
    def get_recipe_output(self):
        if not self.recipe or not self.recipe.outputs:
            return None, 0
        return next(iter(self.recipe.outputs.items()))
    
    def can_process(self):
        if not self.recipe:
            return False

        # Check inputs
        for item_id, amount in self.get_recipe_inputs().items():
            if self.input_inventory.get_amount(item_id) < amount:
                return False

        # Check output capacity (still single output slot)
        for item_id, amount in self.get_recipe_outputs().items():
            if not self.output_inventory.can_add_items(item_id, amount):
                return False

        return True


    def transfer_processing_items_to_player(self, player_inventory):
        if not player_inventory: return

        # Inputs
        for row in self.input_inventory.slots:
            for slot in row:
                if slot: player_inventory.add_items(slot["item"], slot["amount"])
        # Outputs
        for row in self.output_inventory.slots:
            for slot in row:
                if slot: player_inventory.add_items(slot["item"], slot["amount"])

        self.input_inventory = Inventory(1, 1)
        self.output_inventory = Inventory(1, 1)

    def set_recipe(self, recipe, player_inventory=None):
        self.transfer_processing_items_to_player(player_inventory)

        self.recipe = recipe
        self.process_time = recipe.process_time
        self.processing = False
        self.process_timer = 0.0

        # Resize inventories
        input_slots = recipe.input_length
        self.input_inventory = Inventory(slot_width=input_slots, slot_height=1)
        self.output_inventory = Inventory(slot_width=1, slot_height=1)


    # Up here is fine (i think)

    def push_output_item(self, peek=False):
        slot = self.output_inventory.slots[0][0]
        if not slot:
            return None

        item_obj = get_item_by_id(slot["item"])

        if not peek:
            slot["amount"] -= 1
            if slot["amount"] <= 0:
                self.output_inventory.slots[0][0] = None

        return item_obj



    # Under here is fine (i think)

    def update(self, dt):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        if self.processing:
            self.process_timer += dt

            if self.process_timer >= self.process_time:
                # Remove ALL inputs
                for item_id, amount in self.get_recipe_inputs().items():
                    self.input_inventory.remove(item_id, amount)

                # Add ALL outputs (even if currently just one)
                for item_id, amount in self.get_recipe_outputs().items():
                    self.output_inventory.add_items(item_id, amount)

                self.processing = False
                self.process_timer = 0.0


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
        if blocked or not player_inventory.has_enough_build_cost_items(cls.BUILD_COST): ghost.fill((255, 0, 0, 80), special_flags=py.BLEND_RGBA_MULT)
        screen.blit(ghost, (pos[0] - camera.x - cls.SIZE // 2, pos[1] - camera.y - cls.SIZE // 2))
