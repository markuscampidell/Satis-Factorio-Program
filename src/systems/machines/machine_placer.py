import pygame as py
from objects.conveyors.conveyor_belt import BeltSegment
from objects.machines.splitter import Splitter
from core.vector2 import Vector2

class MachinePlacer:
    def __init__(self, world, player, grid, camera, screen_width, screen_height, screen, machine_ui, game=None, splitter_rotation_steps=0):
        self.world = world
        self.player = player
        self.grid = grid
        self.camera = camera
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = screen
        self.machine_ui = machine_ui
        self.game = game
        self.splitter_rotation_steps = splitter_rotation_steps
        self.preview_machine = None
        self.just_placed_machine = False

    def place_machine(self, selected_machine_class):
        """
        Places the selected machine in the world.
        Handles rotation for splitters according to self.splitter_rotation_steps.
        """
        if selected_machine_class is None:
            return

        (snapped_x, snapped_y), blocked = self.get_machine_placement_preview(selected_machine_class)
        if blocked:
            return

        cost = selected_machine_class.BUILD_COST
        if not self.player.inventory.has_enough_items(cost): return

        self.player.inventory.try_remove_items(cost)

        # Splitter placement with rotation
        if selected_machine_class.__name__ == "Splitter":
            from objects.machines.splitter import Splitter

            # Determine direction from rotation steps
            direction_map = [
                Vector2(1, 0),   # 0°
                Vector2(0, 1),   # 90°
                Vector2(-1, 0),  # 180°
                Vector2(0, -1)   # 270°
            ]
            direction = direction_map[self.game.splitter_rotation_steps]

            splitter = Splitter(pos=(snapped_x, snapped_y), direction=direction)
            splitter.rotation_angle = self.game.splitter_rotation_steps * 90
            splitter.image = py.transform.rotate(splitter.image_original, -splitter.rotation_angle)
            splitter.rect = splitter.image.get_rect(center=(snapped_x, snapped_y))

            # Set outputs to belts
            cell_size = self.grid.CELL_SIZE
            splitter.output_belts = []
            for dir_vec in splitter._get_relative_dirs():
                next_rect = splitter.rect.move(int(dir_vec.x * cell_size), int(dir_vec.y * cell_size))
                seg = self.world.belt_map.get((next_rect.x, next_rect.y))
                if seg:
                    splitter.output_belts.append(seg)

            splitter.current_output_index %= max(len(splitter.output_belts), 1)
            self.world.machines.append(splitter)
            self.preview_machine = None

        # Other machines (producing machines)
        else:
            self.world.machines.append(selected_machine_class(pos=(snapped_x, snapped_y)))

        self.just_placed_machine = True
        self.machine_ui.close()

    def delete_machine(self, mx, my):
        world_x, world_y = mx + self.camera.x, my + self.camera.y

        for machine in self.world.machines:
            if machine.rect.collidepoint(world_x, world_y):
                if self.machine_ui.selected_machine == machine:
                    self.machine_ui.close()
                if hasattr(machine, "transfer_processing_items_to_player"):
                    machine.transfer_processing_items_to_player(self.player.inventory)
                if machine.__class__.__name__ == "Splitter" and getattr(machine, "current_item", None):
                    self.player.inventory.try_add_items(machine.current_item, 1)
                    machine.current_item = None
                for item_id, amount in machine.BUILD_COST.items():
                    self.player.inventory.try_add_items(item_id, amount)
                self.world.machines.remove(machine)
                return

    def get_machine_placement_preview(self, selected_machine_class):
        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y
        cell = self.grid.CELL_SIZE

        snapped_x = (world_x // cell) * cell + cell // 2
        snapped_y = (world_y // cell) * cell + cell // 2

        temp_machine_rect = py.Rect(0, 0, selected_machine_class.SIZE, selected_machine_class.SIZE)
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
        """
        Draws a ghost preview for the selected machine.
        Handles rotation for Splitters only.
        """
        if selected_machine_class is None or build_mode != 'building': return
        if selected_machine_class is BeltSegment: return

        mx, my = py.mouse.get_pos()
        world_x, world_y = mx + self.camera.x, my + self.camera.y
        cell = self.grid.CELL_SIZE
        snapped_x = (world_x // cell) * cell + cell // 2
        snapped_y = (world_y // cell) * cell + cell // 2

        temp_rect = py.Rect(0, 0, selected_machine_class.SIZE, selected_machine_class.SIZE)
        temp_rect.center = (snapped_x, snapped_y)
        blocked = self.world.is_rect_blocked(temp_rect)

        # Load/cached ghost image
        if not hasattr(selected_machine_class, "_ghost_image"):
            ghost = py.Surface((selected_machine_class.SIZE, selected_machine_class.SIZE), py.SRCALPHA)
            if selected_machine_class.SPRITE_PATH:
                original = py.image.load(selected_machine_class.SPRITE_PATH).convert_alpha()
                ghost.blit(
                    py.transform.scale(original, (selected_machine_class.SIZE, selected_machine_class.SIZE)),
                    (0, 0)
                )
            selected_machine_class._ghost_image = ghost

        ghost = selected_machine_class._ghost_image.copy()

        # Rotate ghost if it's a splitter
        if selected_machine_class is Splitter:
            ghost = py.transform.rotate(ghost, -90 * rotation_steps)

        ghost.set_alpha(120)

        # Blocked overlay
        if blocked:
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 0, 0, 120))
            ghost.blit(overlay, (0, 0))

        # Can't afford overlay
        if not self.player.inventory.has_enough_items(selected_machine_class.BUILD_COST):
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill((255, 255, 0, 120))
            ghost.blit(overlay, (0, 0))

        # Draw if inside camera
        ghost_rect = py.Rect(
            snapped_x - ghost.get_width() // 2,
            snapped_y - ghost.get_height() // 2,
            ghost.get_width(),
            ghost.get_height()
        )
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.screen_width, self.screen_height)
        if ghost_rect.colliderect(camera_rect):
            self.screen.blit(ghost, (ghost_rect.x - self.camera.x, ghost_rect.y - self.camera.y))
