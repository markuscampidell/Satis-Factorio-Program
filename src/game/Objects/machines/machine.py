import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory

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

        # Separate inventory for each input type
        self.input_inventories = {}
        if recipe:
            for item_id in recipe.inputs:
                self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)

        self.output_inventory = Inventory(slot_width=1, slot_height=1)
        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

    def get_recipe_inputs(self):
            if not self.recipe or not self.recipe.inputs:
                return {}
            return self.recipe.inputs

    def get_recipe_outputs(self):
        if not self.recipe or not self.recipe.outputs:
            return {}
        return self.recipe.outputs

    
    def can_process(self):
        if not self.recipe:
            return False

        # Check each input inventory has enough
        for item_id, amount in self.recipe.inputs.items():
            if self.input_inventories[item_id].get_amount(item_id) < amount:
                return False

        # Check output inventory has space
        for item_id, amount in self.recipe.outputs.items():
            if not self.output_inventory.can_add_items(item_id, amount):
                return False

        return True


    def transfer_processing_items_to_player(self, player_inventory):
        if not player_inventory:
            return

        # Return all items from input inventories
        for inv in self.input_inventories.values():
            for row in inv.slots:
                for slot in row:
                    if slot:
                        player_inventory.add_items(slot["item"], slot["amount"])

        # Return all items from output inventory
        for row in self.output_inventory.slots:
            for slot in row:
                if slot:
                    player_inventory.add_items(slot["item"], slot["amount"])

        # Reset inventories
        for item_id in self.input_inventories:
            self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)
        self.output_inventory = Inventory(slot_width=1, slot_height=1)

    def set_recipe(self, recipe, player_inventory=None):
        # Give player back any existing inputs and outputs
        self.transfer_processing_items_to_player(player_inventory)

        self.recipe = recipe
        self.process_time = recipe.process_time
        self.processing = False
        self.process_timer = 0.0

        # Reset input inventories: one inventory per input type
        self.input_inventories = {}
        for item_id in recipe.inputs:
            self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)

        # Reset output inventory
        self.output_inventory = Inventory(slot_width=1, slot_height=1)


    # Up here is fine (i think)

    # in your machine class
    def push_output_item(self, peek=False):
        for row in self.output_inventory.slots:
            for i, slot in enumerate(row):
                if slot and slot["amount"] > 0:  # <- must check amount
                    item_obj = get_item_by_id(slot["item"])
                    if peek:
                        return item_obj
                    else:
                        slot["amount"] -= 1
                        if slot["amount"] == 0:
                            row[i] = None  # clear slot if empty
                        return item_obj
        return None





    # Under here is fine (i think)

    def update(self, dt):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0
        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                # Remove Inputs / Add Outputs
                for item_id, amount in self.recipe.inputs.items():
                    self.input_inventories[item_id].remove(item_id, amount)
                for item_id, amount in self.recipe.outputs.items():
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
