import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory
from core.vector2 import Vector2
from game.Objects.machines.machine_inventory_ui import MachineInventory

import pygame as py
from constants.itemdata import get_item_by_id
from game.Objects.machines.machine_inventory_ui import MachineInventory

class Machine:
    SIZE = 96
    SPRITE_PATH = None
    BUILD_COST = {}

    def __init__(self, pos, recipe):
        self.recipe = recipe

        # --- Machine sprite ---
        if self.SPRITE_PATH:
            original = py.image.load(self.SPRITE_PATH).convert_alpha()
            w, h = original.get_size()
            image = py.transform.scale(original, (w * 2, h * 2))
            self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
            self.image.blit(image, (0, 0))
            self.rect = self.image.get_rect(center=pos)
        else:
            self.image = py.Surface((self.SIZE, self.SIZE), py.SRCALPHA)
            self.rect = self.image.get_rect(center=pos)

        # --- Inventories (slot-per-item) ---
        # Each input slot matches one recipe input
        self.input_inventory = MachineInventory(list(recipe.inputs.keys()))
        # Each output slot matches one recipe output
        self.output_inventory = MachineInventory(list(recipe.outputs.keys()))

        # --- Processing ---
        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time
        self.output_dir = 0  # 0=right, 1=down, 2=left, 3=up

    # --- Check if machine can start processing ---
    def can_process(self):
        # Check all input slots have enough items
        for item_id, required_amount in self.recipe.inputs.items():
            if self.input_inventory.get_total_amount(item_id) < required_amount:
                return False

        # Check output slots can accept the produced items
        for item_id, output_amount in self.recipe.outputs.items():
            if not self.output_inventory.can_add(item_id, output_amount):
                return False

        return True

    # --- Process machine logic ---
    def update(self, dt):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                # Subtract inputs
                for item_id, amount in self.recipe.inputs.items():
                    self.input_inventory.remove_item(item_id, amount)
                # Add outputs
                for item_id, amount in self.recipe.outputs.items():
                    self.output_inventory.add_item(item_id, amount)
                self.processing = False
                self.process_timer = 0.0

    # --- Transfer all items to player inventory ---
    def transfer_processing_items_to_player(self, player_inventory=None):
        if not player_inventory:
            return

        # Transfer inputs
        for slot in self.input_inventory.slots:
            if slot.amount > 0:
                item = get_item_by_id(slot.allowed_item_id)
                if item:
                    player_inventory.add_items(item, slot.amount)
                slot.amount = 0

        # Transfer outputs
        for slot in self.output_inventory.slots:
            if slot.amount > 0:
                item = get_item_by_id(slot.allowed_item_id)
                if item:
                    player_inventory.add_items(item, slot.amount)
                slot.amount = 0

    # --- Change recipe ---
    def set_recipe(self, recipe, player_inventory=None):
        # Transfer current items to player first
        self.transfer_processing_items_to_player(player_inventory)

        # Set new recipe and inventories
        self.recipe = recipe
        self.input_inventory = MachineInventory(list(recipe.inputs.keys()))
        self.output_inventory = MachineInventory(list(recipe.outputs.keys()))
        self.processing = False
        self.process_timer = 0.0

    # --- Draw machine ---
    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.x, self.rect.y - camera.y))

    # --- Pop one output item from the machine ---
    def push_output_item(self, peek=False):
        for slot in self.output_inventory.slots:
            if slot.amount > 0:
                item_obj = get_item_by_id(slot.allowed_item_id)
                if not peek:
                    slot.remove(1)
                return item_obj
        return None

    # --- Draw ghost machine for placement ---
    @classmethod
    def draw_ghost_machine(cls, screen, camera, pos, blocked, player_inventory):
        if cls.SPRITE_PATH is None:
            return

        original = py.image.load(cls.SPRITE_PATH).convert_alpha()
        w, h = original.get_size()
        image = py.transform.scale(original, (w * 2, h * 2))

        ghost = py.Surface((cls.SIZE, cls.SIZE), py.SRCALPHA)
        ghost.blit(image, (0, 0))
        ghost.set_alpha(120)

        if blocked or not player_inventory.has_enough_build_cost_items(cls.BUILD_COST):
            ghost.fill((255, 0, 0, 80), special_flags=py.BLEND_RGBA_MULT)

        screen.blit(ghost, (pos[0] - camera.x - cls.SIZE // 2, pos[1] - camera.y - cls.SIZE // 2))
