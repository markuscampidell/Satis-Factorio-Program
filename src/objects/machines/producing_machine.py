# objects.machines.producing_machine
import pygame as py

from constants.itemdata import get_item_by_id
from core.vector2 import Vector2
from entities.inventory import Inventory
from objects.machines.machine import Machine

from game.grid import Grid

class ProducingMachine(Machine):
    # Visual speed (tiles/sec) items travel from the input edge to the
    # machine center, matching a basic belt so it reads as "a belt inside".
    INPUT_ANIM_TILES_PER_SEC = 2.0

    def __init__(self, grid_pos, recipe=None, cell_size=Grid.CELL_SIZE):
        super().__init__(grid_pos, cell_size)
        self.recipe = recipe

        self.processing = False
        self.process_timer = 0.0
        self.process_time = recipe.process_time if recipe else 1.0

        self.cell_size = cell_size

        # Purely visual: items animating from the input edge to the
        # machine center after they've already been added to the inventory.
        self.input_animations = []

        if recipe:
            self._reset_inventories(recipe)

    def update(self, dt, belt_map=None, machine_map=None):
        if not self.processing and self.can_process():
            self.processing = True
            self.process_timer = 0.0

        if self.processing:
            self.process_timer += dt
            if self.process_timer >= self.process_time:
                self._complete_process()
                self.processing = False
                self.process_timer = 0.0

        self._update_input_animations(dt)
        self.push_output(belt_map or {}, machine_map or {})

    def push_output(self, belt_map, machine_map):
        """Push one item from output inventories onto whatever's at an
        output tile - a belt, a splitter, or another machine. Tries each
        output direction in turn for the first available output item."""
        for item_id, inv in self.output_inventories.items():
            for row in inv.slots:
                for i, slot in enumerate(row):
                    if not (slot and slot["amount"] > 0):
                        continue

                    item_obj = get_item_by_id(slot["item"])

                    for (dx, dy), push_direction in self._get_output_tiles():
                        tile_pos = (self.grid_pos[0] + dx, self.grid_pos[1] + dy)

                        if self._try_push_to_tile(item_obj, push_direction, tile_pos, belt_map, machine_map):
                            slot["amount"] -= 1
                            if slot["amount"] == 0:
                                row[i] = None
                            return True

        return False

    def _try_push_to_tile(self, item_obj, push_direction, tile_pos, belt_map, machine_map):
        belt = belt_map.get(tile_pos)
        if belt is not None:
            # Only a belt facing directly away from us (same direction as
            # the push) accepts - not perpendicular, not facing back in.
            if belt.item is not None or belt.direction != push_direction:
                return False

            belt.item = item_obj
            belt.item_progress = 0.0
            belt.current_incoming_direction = push_direction
            return True

        machine = machine_map.get(tile_pos)
        if machine is None:
            return False

        # Duck-typed dispatch (not isinstance) to avoid a circular import
        # with Splitter, which already imports ProducingMachine. Splitter
        # exposes receive_item, ProducingMachine exposes try_receive_item -
        # whichever is there gets a shot with its own existing acceptance
        # rules (direction match for a splitter, recipe-input match and
        # space for a machine).
        if hasattr(machine, "receive_item"):
            return machine.receive_item(item_obj, incoming_direction=push_direction)
        if hasattr(machine, "try_receive_item"):
            return machine.try_receive_item(item_obj, self.grid_pos)

        return False

    def try_receive_item(self, item, source_grid_pos):
        """Try to add `item` to whichever input inventory actually needs
        it (matches the recipe input and has room). Triggers the visual
        "item traveling in" animation on success. Single entry point used
        by both belts and splitters feeding this machine, so both get
        identical acceptance rules and the same animation."""
        inv = self.input_inventories.get(item.item_id)
        if inv is None:
            return False

        if not inv.try_add_items(item, 1):
            return False

        self.start_input_animation(item, source_grid_pos)
        return True

    def start_input_animation(self, item, source_grid_pos):
        """Play a visual-only animation of `item` moving from source_grid_pos
        (the belt tile it came from, one tile before the machine's edge) to
        the machine's center, matching the normal belt-to-belt transport
        animation. Call this after the item has already been added to the
        input inventory."""
        entry_x = source_grid_pos[0] * self.cell_size + self.cell_size // 2
        entry_y = source_grid_pos[1] * self.cell_size + self.cell_size // 2
        target_x = self.grid_pos[0] * self.cell_size + (self.WIDTH * self.cell_size) // 2
        target_y = self.grid_pos[1] * self.cell_size + (self.HEIGHT * self.cell_size) // 2

        distance = ((target_x - entry_x) ** 2 + (target_y - entry_y) ** 2) ** 0.5
        speed_pixels_per_sec = self.INPUT_ANIM_TILES_PER_SEC * self.cell_size
        duration = max(distance / speed_pixels_per_sec, 0.001)

        self.input_animations.append({
            "item": item,
            "start": (entry_x, entry_y),
            "end": (target_x, target_y),
            "progress": 0.0,
            "duration": duration,
        })

    def _update_input_animations(self, dt):
        if not self.input_animations:
            return
        for anim in self.input_animations:
            anim["progress"] += dt / anim["duration"]
        self.input_animations = [a for a in self.input_animations if a["progress"] < 1.0]

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

    def _get_output_tiles(self):
        """(tile_offset, direction) for every tile around the machine's
        entire perimeter - it can push output out any side, not just one
        fixed tile. tile_offset is relative to grid_pos (top-left
        corner); direction is the unit vector pointing outward through
        that tile."""
        tiles = []

        for dy in range(self.HEIGHT):
            tiles.append(((self.WIDTH, dy), Vector2(1, 0)))    # right edge
            tiles.append(((-1, dy), Vector2(-1, 0)))           # left edge

        for dx in range(self.WIDTH):
            tiles.append(((dx, -1), Vector2(0, -1)))           # top edge
            tiles.append(((dx, self.HEIGHT), Vector2(0, 1)))   # bottom edge

        return tiles

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