# systems.rendering.ghost_machine_renderer
import pygame as py

from objects.conveyors.belt_segment import BeltSegment


class GhostMachineRenderer:
    """Draws the translucent placement preview for the currently selected machine class."""

    def __init__(self, world, player, camera, grid, screen):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.screen = screen

    def draw(self, selected_machine_class=None, build_mode=None, rotation_steps=0):
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
