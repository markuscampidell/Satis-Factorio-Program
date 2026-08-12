# systems.machines.machine_system
import pygame as py

from objects.machines.splitter import Splitter
from core.vector2 import Vector2
from systems.conveyors.belt_system import BeltSystem

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

        cost = selected_machine_class.BUILD_COST

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

        cells = getattr(machine, "occupied_cells", [])
        allow_replace = bool(py.key.get_mods() & py.KMOD_SHIFT)

        # The player always blocks. A belt or machine tile only blocks if
        # we're not allowed to replace it (shift held).
        if any(self.world.is_blocked_by_player(cell) for cell in cells):
            return
        if not allow_replace and any(self.world.is_cell_blocked(cell) for cell in cells):
            return

        replaced_segments, replaced_machines = self.world.gather_occupants(cells)

        # Simulate the whole operation first - no lost items, no partial
        # placement if a refund doesn't fit or the cost isn't affordable.
        scratch = self.player.inventory.clone()
        if not BeltSystem.apply_refunds(scratch, replaced_segments, replaced_machines):
            return
        if not scratch.try_remove_items(cost):
            return

        # Simulation succeeded exactly as it will for real - apply it.
        BeltSystem.apply_refunds(self.player.inventory, replaced_segments, replaced_machines)
        for old_seg in replaced_segments:
            old_seg._clear_item()
            self.world.remove_belt_segment(old_seg)
        for old_machine in replaced_machines:
            self.world.remove_machine(old_machine)

        self.player.inventory.try_remove_items(cost)
        self.world.add_machine(machine)
        self.preview_machine = None
        self.just_placed_machine = True

    def can_afford_deletion(self, machine):
        """True if the player's inventory has room for everything this
        machine would refund (build cost plus whatever it's holding)."""
        scratch = self.player.inventory.clone()
        return BeltSystem.apply_refunds(scratch, [], [machine])

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