# systems.machines.machine_system
import pygame as py

from objects.conveyors.belt_segment import BeltSegment
from objects.machines.splitter import Splitter
from core.vector2 import Vector2

class MachineSystem:
    def __init__(self, world, player, camera, grid, screen):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.screen = screen

        self.preview_machine = None
        self.just_placed_machine = False
        self.splitter_rotation_steps = 0

    # -----------------------------
    # Place machine
    # -----------------------------
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

    # -----------------------------
    # Delete machine
    # -----------------------------
    def delete_machine(self, mx, my):
        grid_x, grid_y = self.world.snap_to_tile(mx + self.camera.x, my + self.camera.y)

        for machine in list(self.world.machines):
            if (grid_x, grid_y) in getattr(machine, "occupied_cells", []):
                if hasattr(machine, "transfer_processing_items_to_player"):
                    machine.transfer_processing_items_to_player(self.player.inventory)

                if machine.__class__.__name__ == "Splitter" and getattr(machine, "current_item", None):
                    self.player.inventory.try_add_items(machine.current_item, 1)
                    machine.current_item = None

                # Refund cost
                for item_id, amount in machine.BUILD_COST.items():
                    self.player.inventory.try_add_items(item_id, amount)

                self.world.remove_machine(machine)
                return

    # -----------------------------
    # Placement preview
    # -----------------------------
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

    # -----------------------------
    # Ghost machine rendering
    # -----------------------------
    def ghost_machine(self, selected_machine_class=None, build_mode=None, rotation_steps=0):
        if selected_machine_class is None or build_mode != 'building':
            return
        if selected_machine_class is BeltSegment:
            return

        mx, my = py.mouse.get_pos()
        grid_x, grid_y = self.world.snap_to_tile(mx + self.camera.x, my + self.camera.y)

        width, height = selected_machine_class.WIDTH, selected_machine_class.HEIGHT
        top_left_x = grid_x - width // 2
        top_left_y = grid_y - height // 2

        # Tile-based blocked check
        temp_machine = selected_machine_class(grid_pos=(top_left_x, top_left_y))
        blocked = any(self.world.is_cell_blocked(cell) or self.world.is_blocked_by_player(cell)
                      for cell in getattr(temp_machine, "occupied_cells", []))

        # Create ghost surface (cached)
        pixel_width = width * self.grid.CELL_SIZE
        pixel_height = height * self.grid.CELL_SIZE
        cache_key = f"_ghost_image_{width}x{height}"

        if not hasattr(selected_machine_class, cache_key):
            ghost = py.Surface((pixel_width, pixel_height), py.SRCALPHA)
            if selected_machine_class.SPRITE_PATH:
                original = py.image.load(selected_machine_class.SPRITE_PATH).convert_alpha()
                scaled = py.transform.scale(original, (pixel_width, pixel_height))
                ghost.blit(scaled, (0, 0))
            setattr(selected_machine_class, cache_key, ghost)

        ghost = getattr(selected_machine_class, cache_key).copy()

        if selected_machine_class.__name__ == "Splitter":
            ghost = py.transform.rotate(ghost, -90 * rotation_steps)

        ghost.set_alpha(120)

        # Overlay for blocked tiles (machines, belts, player)
        if blocked:
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 0, 0, 120))
            ghost.blit(overlay, (0, 0))

        # Overlay for missing resources
        if not self.player.inventory.has_enough_items(selected_machine_class.BUILD_COST):
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 255, 0, 120))
            ghost.blit(overlay, (0, 0))

        # Draw at pixel position for camera
        pixel_x = top_left_x * self.grid.CELL_SIZE
        pixel_y = top_left_y * self.grid.CELL_SIZE
        self.screen.blit(ghost, (pixel_x - self.camera.x, pixel_y - self.camera.y))