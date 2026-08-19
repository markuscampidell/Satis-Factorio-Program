# objects.machines.producing_machine
import pygame as py

from constants.itemdata import get_item_by_id
from core.vector2 import Vector2
from entities.inventory import Inventory
from objects.machines.machine import Machine
from objects.machines.machine_output_pusher import push_output
from objects.machines.input_animator import InputAnimator

from game.grid import Grid

class ProducingMachine(Machine):
    def __init__(self, grid_pos, recipe=None, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)
        self.recipe = recipe

        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

        self.cell_size = cell_size

        # Purely visual: items animating from the input edge to the
        # machine center after they've already been added to the inventory.
        self.input_animator = InputAnimator(cell_size)

        if recipe:
            self._reset_inventories(recipe)

    def update(self, dt, belt_map=None, machine_map=None):
        self._update_processing(dt)
        self.input_animator.update(dt)
        push_output(self, belt_map or {}, machine_map or {})

    def _update_processing(self, dt):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                self._complete_process()
                self.processing = False
                self.process_timer = 0.0

    def try_receive_item(self, item, source_grid_pos, source_speed=None):
        """Try to add `item` to whichever input inventory actually needs
        it (matches the recipe input and has room). Triggers the visual
        "item traveling in" animation on success. Single entry point used
        by both belts and splitters feeding this machine, so both get
        identical acceptance rules and the same animation. `source_speed`
        is the feeding belt's tiles/sec, if there is one, so the animation
        matches how fast that belt actually moves."""
        inv = self.input_inventories.get(item.item_id)
        if inv is None:
            return False

        if not inv.try_add_items(item, 1):
            return False

        self.input_animator.start(item, source_grid_pos, self.grid_pos, self.WIDTH, self.HEIGHT, tiles_per_sec=source_speed)
        return True

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

    def get_refund_items(self):
        refund = super().get_refund_items()
        for inv in list(self.input_inventories.values()) + list(self.output_inventories.values()):
            for row in inv.slots:
                for slot in row:
                    if slot:
                        refund[slot["item"]] = refund.get(slot["item"], 0) + slot["amount"]
        return refund

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


    def draw(self, screen, camera):
        if not self.image:
            return

        pixel_x = self.grid_pos[0] * self.cell_size - camera.x
        pixel_y = self.grid_pos[1] * self.cell_size - camera.y
        width = self.WIDTH * self.cell_size
        height = self.HEIGHT * self.cell_size

        # Image is already scaled to machine dimensions in Machine.__init__
        if self.image:
            screen.blit(self.image, (pixel_x, pixel_y))

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