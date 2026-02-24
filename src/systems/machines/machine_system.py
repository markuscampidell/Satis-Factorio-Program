import pygame as py
from objects.conveyors.belt_segment import BeltSegment
from objects.machines.splitter import Splitter
from core.vector2 import Vector2

class MachineSystem:
    def __init__(self, world, player, grid, camera, screen, machine_ui, game=None, splitter_rotation_steps=0):
        self.world = world
        self.player = player
        self.grid = grid
        self.camera = camera
        self.screen = screen
        self.machine_ui = machine_ui
        self.game = game
        self.splitter_rotation_steps = splitter_rotation_steps
        self.preview_machine = None
        self.just_placed_machine = False

    def place_machine(self, selected_machine_class):
        if selected_machine_class is None: return
        (snapped_x, snapped_y), blocked = self.get_machine_placement_preview(selected_machine_class)
        if blocked: return

        cost = selected_machine_class.BUILD_COST
        if not self.player.inventory.has_enough_items(cost): return
        self.player.inventory.try_remove_items(cost)

        if selected_machine_class.__name__ == "Splitter":
            direction_map = [Vector2(1, 0),
                             Vector2(0, 1),
                             Vector2(-1, 0),
                             Vector2(0, -1)]

            direction = direction_map[self.game.splitter_rotation_steps]

            machine = Splitter(pos=(snapped_x, snapped_y), direction=direction)
            machine.rotation_angle = self.game.splitter_rotation_steps * 90
            machine.image = py.transform.rotate(machine.image_original, -machine.rotation_angle)
            machine.rect = machine.image.get_rect(center=(snapped_x, snapped_y))

            cell_size = self.grid.CELL_SIZE
            machine.output_belts = []

            for dir_vec in machine._get_relative_dirs():
                next_rect = machine.rect.move(int(dir_vec.x * cell_size),
                                              int(dir_vec.y * cell_size))
                seg = self.world.belt_map.get((next_rect.x, next_rect.y))
                if seg:
                    machine.output_belts.append(seg)

            machine.current_output_index %= max(len(machine.output_belts), 1)

        else:
            machine = selected_machine_class(pos=(snapped_x, snapped_y))

        self.world.add_machine(machine)

        self.preview_machine = None
        self.just_placed_machine = True
        self.machine_ui.close()

    def delete_machine(self, mx, my):
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        for machine in list(self.world.machines):
            if machine.rect.collidepoint(world_x, world_y):
                if hasattr(machine, "transfer_processing_items_to_player"):
                    machine.transfer_processing_items_to_player(self.player.inventory)

                if machine.__class__.__name__ == "Splitter":
                    if getattr(machine, "current_item", None):
                        self.player.inventory.try_add_items(machine.current_item, 1)
                        machine.current_item = None

                for item_id, amount in machine.BUILD_COST.items():
                    self.player.inventory.try_add_items(item_id, amount)

                self.world.remove_machine(machine)
                return

    def get_machine_placement_preview(self, selected_machine_class):
        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y

        cell = self.grid.CELL_SIZE
        width_cells = selected_machine_class.WIDTH
        height_cells = selected_machine_class.HEIGHT

        pixel_width = width_cells * cell
        pixel_height = height_cells * cell

        # Determine top-left grid position
        if width_cells % 2 == 0:
            snapped_tl_x = (world_x // cell) * cell
        else:
            center_cell_x = world_x // cell
            snapped_tl_x = (center_cell_x - width_cells // 2) * cell

        if height_cells % 2 == 0:
            snapped_tl_y = (world_y // cell) * cell
        else:
            center_cell_y = world_y // cell
            snapped_tl_y = (center_cell_y - height_cells // 2) * cell

        snapped_x = snapped_tl_x + pixel_width // 2
        snapped_y = snapped_tl_y + pixel_height // 2

        temp_machine_rect = py.Rect(0, 0, pixel_width, pixel_height)
        temp_machine_rect.center = (snapped_x, snapped_y)

        blocked = False

        if self.player.rect.colliderect(temp_machine_rect):
            blocked = True

        for machine in self.world.machines:
            if machine.rect.colliderect(temp_machine_rect):
                blocked = True
                break

        if not blocked:
            for seg in self.world.belt_segments:
                if seg.rect.colliderect(temp_machine_rect):
                    blocked = True
                    break

        return (snapped_x, snapped_y), blocked
    
    def ghost_machine(self, selected_machine_class=None, build_mode=None, rotation_steps=0):
        if selected_machine_class is None or build_mode != 'building': return
        if selected_machine_class is BeltSegment: return

        (snapped_x, snapped_y), blocked = self.get_machine_placement_preview(selected_machine_class)

        cell = self.grid.CELL_SIZE
        width_cells = selected_machine_class.WIDTH
        height_cells = selected_machine_class.HEIGHT

        pixel_width = width_cells * cell
        pixel_height = height_cells * cell

        # Create and cache ghost image if needed
        cache_key = f"_ghost_image_{width_cells}x{height_cells}"

        if not hasattr(selected_machine_class, cache_key):
            ghost = py.Surface((pixel_width, pixel_height), py.SRCALPHA)

            if selected_machine_class.SPRITE_PATH:
                original = py.image.load(selected_machine_class.SPRITE_PATH).convert_alpha()
                scaled = py.transform.scale(original, (pixel_width, pixel_height))
                ghost.blit(scaled, (0, 0))

            setattr(selected_machine_class, cache_key, ghost)

        ghost = getattr(selected_machine_class, cache_key).copy()

        if selected_machine_class is Splitter:
            ghost = py.transform.rotate(ghost, -90 * rotation_steps)

        ghost.set_alpha(120)

        if blocked:
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 0, 0, 120))
            ghost.blit(overlay, (0, 0))

        if not self.player.inventory.has_enough_items(selected_machine_class.BUILD_COST):
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 255, 0, 120))
            ghost.blit(overlay, (0, 0))

        # Draw if inside camera
        ghost_rect = ghost.get_rect(center=(snapped_x, snapped_y))

        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        if ghost_rect.colliderect(camera_rect):
            self.screen.blit(ghost, (ghost_rect.x - self.camera.x, ghost_rect.y - self.camera.y))