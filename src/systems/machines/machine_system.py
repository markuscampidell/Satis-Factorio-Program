# systems.machines.machine_system
import pygame as py

from objects.machines.splitter import Splitter
from core.vector2 import Vector2

class MachineSystem:
    def __init__(self, world, player, camera, grid):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid

        self.preview_machine = None
        self.just_placed_machine = False
        self.splitter_rotation_steps = 0

    def place_machine(self, selected_machine_class):
        if selected_machine_class is None:
            return

        # Snap mouse to grid
        mx, my = py.mouse.get_pos()
        grid_x, grid_y = self.world.snap_to_tile(mx + self.camera.x, my + self.camera.y)

        width, height = selected_machine_class.WIDTH, selected_machine_class.HEIGHT
        top_left_x = grid_x - width // 2
        top_left_y = grid_y - height // 2

        # Check inventory
        cost = selected_machine_class.BUILD_COST
        if not self.player.inventory.has_enough_items(cost):
            return

        # Create machine instance
        if selected_machine_class.__name__ == "Splitter":
            direction_map = [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]
            direction = direction_map[self.splitter_rotation_steps]
            machine = Splitter(grid_pos=(top_left_x, top_left_y), direction=direction)
            machine.rotation_angle = self.splitter_rotation_steps * 90
            machine.image = py.transform.rotate(machine.image_original, -machine.rotation_angle)

            # Compute output belts
            machine.output_belts = []
            for dir_vec in machine._get_relative_dirs():
                next_cell = (top_left_x + dir_vec.x, top_left_y + dir_vec.y)
                seg = self.world.get_belt_segment_at(next_cell[0]*self.grid.CELL_SIZE,
                                                     next_cell[1]*self.grid.CELL_SIZE)
                if seg:
                    machine.output_belts.append(seg)
            machine.current_output_index %= max(len(machine.output_belts), 1)
        else:
            machine = selected_machine_class(grid_pos=(top_left_x, top_left_y))

        # Check for blocked tiles (machines, belts, or player)
        blocked = any(self.world.is_cell_blocked(cell) or self.world.is_blocked_by_player(cell)
                      for cell in getattr(machine, "occupied_cells", []))
        if blocked:
            return

        # Remove items and add machine
        self.player.inventory.try_remove_items(cost)
        self.world.add_machine(machine)
        self.preview_machine = None
        self.just_placed_machine = True

    def can_afford_deletion(self, machine):
        """True if the player's inventory has room for everything this
        machine would refund (build cost plus whatever it's holding)."""
        scratch = self.player.inventory.clone()
        for item_id, amount in machine.get_refund_items().items():
            if not scratch.try_add_items(item_id, amount):
                return False
        return True

    def delete_machine(self, mx, my):
        grid_x, grid_y = self.world.snap_to_tile(mx + self.camera.x, my + self.camera.y)

        for machine in list(self.world.machines):
            if (grid_x, grid_y) in getattr(machine, "occupied_cells", []):
                if not self.can_afford_deletion(machine):
                    return  # Not enough inventory space to receive the refund

                for item_id, amount in machine.get_refund_items().items():
                    self.player.inventory.try_add_items(item_id, amount)

                self.world.remove_machine(machine)
                return

    def get_machine_placement_preview(self, selected_machine_class):
        mx, my = py.mouse.get_pos()
        grid_x, grid_y = self.world.snap_to_tile(mx + self.camera.x, my + self.camera.y)

        width, height = selected_machine_class.WIDTH, selected_machine_class.HEIGHT
        top_left_x = grid_x - width // 2
        top_left_y = grid_y - height // 2

        temp_machine = selected_machine_class(grid_pos=(top_left_x, top_left_y))

        blocked = any(self.world.is_cell_blocked(cell) or self.world.is_blocked_by_player(cell)
                      for cell in getattr(temp_machine, "occupied_cells", []))

        return (top_left_x, top_left_y), blocked