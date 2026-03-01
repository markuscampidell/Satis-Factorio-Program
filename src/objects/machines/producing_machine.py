# objects.machines.producing_machine
import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory import Inventory
from objects.machines.machine import Machine

from game.grid import Grid

class ProducingMachine(Machine):
    def __init__(self, grid_pos, recipe=None, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)
        self.recipe = recipe

        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

        self.cell_size = cell_size

        # Tile-based output tracking
        self.output_belts = []
        self.current_output_index = 0

        if recipe:
            self._reset_inventories(recipe)

    def update(self, dt, belt_map=None):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                self._complete_process()
                self.processing = False
                self.process_timer = 0.0

    def _complete_process(self):
        # Remove inputs
        for item_id, amount in self.recipe.inputs.items():
            self.input_inventories[item_id].try_remove_item(item_id, amount)
        # Add outputs
        for item_id, amount in self.recipe.outputs.items():
            self.output_inventories[item_id].try_add_items(item_id, amount)

    def can_process(self):
        if not self.recipe:
            return False
        # Check inputs
        for item_id, amount in self.recipe.inputs.items():
            if self.input_inventories[item_id].get_amount(item_id) < amount:
                return False
        # Check outputs
        for item_id, amount in self.recipe.outputs.items():
            if not self.output_inventories[item_id].can_add_items(item_id, amount):
                return False
        return True
    
    def _reset_inventories(self, recipe):
        self.input_inventories = {item_id: Inventory(slot_width=1, slot_height=1) for item_id in recipe.inputs}
        self.output_inventories = {item_id: Inventory(slot_width=1, slot_height=1) for item_id in recipe.outputs}
    
    def set_recipe(self, recipe, player_inventory):
        # Inputs
        if hasattr(self, "input_inventories"):
            for item_id, inv in self.input_inventories.items():
                for row in inv.slots:
                    for slot in row:
                        if slot:
                            player_inventory.try_add_items(slot["item"], slot["amount"])

        # Outputs
        if hasattr(self, "output_inventories"):
            for item_id, inv in self.output_inventories.items():
                for row in inv.slots:
                    for slot in row:
                        if slot:
                            player_inventory.try_add_items(slot["item"], slot["amount"])

        self.processing = False
        self.process_timer = 0.0

        self.recipe = recipe
        self.process_time = recipe.process_time if recipe else 1.0

        if recipe: self._reset_inventories(recipe)

        self.current_output_index = 0

    def update_outputs(self, belt_map):
        """Tile-based update: find belts in output positions."""
        belts = []
        for dx, dy in self._get_output_dirs():
            tile_pos = (self.grid_pos[0] + dx, self.grid_pos[1] + dy)
            seg = belt_map.get(tile_pos)
            if seg:
                belts.append(seg)
        self.output_belts = belts
        if self.current_output_index >= len(self.output_belts):
            self.current_output_index = 0

    def _get_output_dirs(self):
        """By default, output to the right tile. Override for multi-direction outputs."""
        return [(1, 0)]  # simple: output to the right

    def push_output_item(self):
        """Push one item from output inventories to the next belt (tile-based)."""
        if not self.output_belts:
            return False

        for item_id, inv in self.output_inventories.items():
            for row in inv.slots:
                for i, slot in enumerate(row):
                    if slot and slot["amount"] > 0:
                        item_obj = get_item_by_id(slot["item"])
                        belt = self.output_belts[self.current_output_index % len(self.output_belts)]
                        if belt.item is None:
                            belt.item = item_obj
                            belt.item_progress = 0.0
                            slot["amount"] -= 1
                            if slot["amount"] == 0:
                                row[i] = None
                            self.current_output_index += 1
                            return True
        return False
    
    def draw(self, screen, camera):
        if not self.image:
            return

        pixel_x = self.grid_pos[0] * self.cell_size - camera.x
        pixel_y = self.grid_pos[1] * self.cell_size - camera.y
        width = self.WIDTH * self.cell_size
        height = self.HEIGHT * self.cell_size

        scaled_image = py.transform.scale(self.image, (width, height))
        screen.blit(scaled_image, (pixel_x, pixel_y))

        # Optional: draw outputs for clarity
        self._draw_recipe_outputs(screen, camera)

    def _draw_recipe_outputs(self, screen, camera):
        if not self.recipe or not self.recipe.outputs:
            return
        images = []
        for item_id in self.recipe.outputs:
            item_obj = get_item_by_id(item_id)
            if item_obj and item_obj.sprite:
                images.append(item_obj.sprite)
        if not images:
            return

        spacing = 4
        total_width = sum(img.get_width() for img in images) + spacing * (len(images) - 1)
        center_x = self.grid_pos[0] * self.cell_size + (self.WIDTH * self.cell_size) // 2 - camera.x
        center_y = self.grid_pos[1] * self.cell_size + (self.HEIGHT * self.cell_size) // 2 - camera.y
        start_x = center_x - total_width // 2
        x = start_x
        for img in images:
            y = center_y - img.get_height() // 2
            screen.blit(img, (x, y))
            x += img.get_width() + spacing

    def push_output_items(self, peek=False):
        """Return an item from output inventory (like before)"""
        for item_id, inv in self.output_inventories.items():
            for row in inv.slots:
                for i, slot in enumerate(row):
                    if slot and slot["amount"] > 0:
                        item_obj = get_item_by_id(slot["item"])
                        if peek:
                            return item_obj
                        slot["amount"] -= 1
                        if slot["amount"] == 0:
                            row[i] = None
                        return item_obj
        return None