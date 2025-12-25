import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory

class Machine:
    SPRITE_PATH = None
    SIZE = 96

    def __init__(self, pos, recipe):
        if self.SPRITE_PATH is None:
            raise NotImplementedError("Machine needs a SPRITE_PATH")

        original = py.image.load(self.SPRITE_PATH).convert_alpha()
        w, h = original.get_size()
        image = py.transform.scale(original, (w * 2, h * 2))

        self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        self.image.blit(image, (0, 0))

        self.rect = self.image.get_rect(center=pos)

        # Inventory and processing
        self.recipe = recipe
        self.input_inventory = Inventory()
        self.output_inventory = Inventory()
        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time

    # check if it has enough input items
    def can_process(self):
        for item, amount in self.recipe.inputs.items():
            if self.input_inventory.get_amount(item) < amount:
                return False
        return True

    def update(self, dt):
        # If it can process it processes
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        # Processing itself
        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                # Subtract inputs
                for item, amount in self.recipe.inputs.items():
                    self.input_inventory.remove(item, amount)
                # Add outputs
                for item, amount in self.recipe.outputs.items():
                    self.output_inventory.add(item, amount)

                self.processing = False
                self.process_timer = 0.0

    def transfer_to_player(self, player_inventory=None):
        if player_inventory:
            # Input items
            for item_id, amount in self.input_inventory.items.items():
                item = get_item_by_id(item_id)
                if item:
                    player_inventory.add(item, amount)
            self.input_inventory.items.clear()

            # Output items
            for item_id, amount in self.output_inventory.items.items():
                item = get_item_by_id(item_id)
                if item:
                    player_inventory.add(item, amount)
            self.output_inventory.items.clear()

    def set_recipe(self, recipe, player_inventory=None):
        # Transfer old inputs/outputs to player first
        self.transfer_to_player(player_inventory)

        # Set the new recipe
        self.recipe = recipe
        self.processing = False
        self.process_timer = 0.0

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))