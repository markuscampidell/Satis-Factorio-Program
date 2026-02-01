import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory
from game.Objects.machines.machine import Machine

class ProducingMachine(Machine):
    def __init__(self, pos, recipe=None):
        super().__init__(pos)
        self.recipe = recipe
        self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            image = py.transform.scale(original, (self.SIZE, self.SIZE))
            self.image.blit(image, (0, 0))
        self.rect = self.image.get_rect(center=pos)

        self.input_inventories = {}
        if recipe:
            for item_id in recipe.inputs:
                self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)

        self.output_inventory = Inventory(slot_width=1, slot_height=1)
        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

    def update(self, dt):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0
        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                for item_id, amount in self.recipe.inputs.items():
                    self.input_inventories[item_id].remove_item(item_id, amount)
                for item_id, amount in self.recipe.outputs.items():
                    self.output_inventory.add_items(item_id, amount)
                self.processing = False
                self.process_timer = 0.0

    def get_recipe_inputs(self):
            if not self.recipe or not self.recipe.inputs:
                return {}
            return self.recipe.inputs
    def get_recipe_outputs(self):
        if not self.recipe or not self.recipe.outputs:
            return {}
        return self.recipe.outputs
    
    def outputs_per_minute(self):
        if not self.recipe: return {}
        return {item_id: amount * (60 / self.process_time) for item_id, amount in self.recipe.outputs.items()}
    def inputs_per_minute(self):
        if not self.recipe: return {}
        return {item_id: amount * (60 / self.process_time) for item_id, amount in self.recipe.inputs.items()}

    def can_process(self):
        if not self.recipe: return False

        for item_id, amount in self.recipe.inputs.items():
            if self.input_inventories[item_id].get_amount(item_id) < amount: return False
        for item_id, amount in self.recipe.outputs.items():
            if not self.output_inventory.can_add_items(item_id, amount): return False
        return True
    def transfer_processing_items_to_player(self, player_inventory):
        if not player_inventory: return

        for inv in self.input_inventories.values():
            for row in inv.slots:
                for slot in row:
                    if slot: player_inventory.add_items(slot["item"], slot["amount"])
        for row in self.output_inventory.slots:
            for slot in row:
                if slot: player_inventory.add_items(slot["item"], slot["amount"])
        for item_id in self.input_inventories:
            self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)

        self.output_inventory = Inventory(slot_width=1, slot_height=1)
    def set_recipe(self, recipe, player_inventory=None, dev_mode=False):
        if not dev_mode and player_inventory is not None:
            self.transfer_processing_items_to_player(player_inventory)
        self.recipe = recipe
        self.process_time = recipe.process_time
        self.processing = False
        self.process_timer = 0.0
        self.input_inventories = {}
        for item_id in recipe.inputs:
            self.input_inventories[item_id] = Inventory(slot_width=1, slot_height=1)
        self.output_inventory = Inventory(slot_width=1, slot_height=1)

    def push_output_item(self, peek=False):
        for row in self.output_inventory.slots:
            for i, slot in enumerate(row):
                if slot and slot["amount"] > 0:
                    item_obj = get_item_by_id(slot["item"])
                    if peek: return item_obj
                    else:
                        slot["amount"] -= 1
                        if slot["amount"] == 0:
                            row[i] = None
                        return item_obj
        return None

    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))
        self.draw_recipe_outputs(screen, camera)
    def draw_recipe_outputs(self, screen, camera):
        if not self.recipe: return
        outputs = self.get_recipe_outputs()
        if not outputs: return

        images = []
        for item_id in outputs:
            item_obj = get_item_by_id(item_id)
            if item_obj:
                item_obj.load_sprite()
                if item_obj.image: images.append(item_obj.image)
        if not images: return

        spacing = 4
        total_width = sum(img.get_width() for img in images) + spacing * (len(images) - 1)
        start_x = self.rect.centerx - camera.x - total_width // 2
        x = start_x
        for img in images:
            y = self.rect.centery - camera.y - img.get_height() // 2
            screen.blit(img, (x, y))
            x += img.get_width() + spacing