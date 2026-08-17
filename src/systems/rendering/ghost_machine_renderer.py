# systems.rendering.ghost_machine_renderer
import pygame as py

from core.vector2 import Vector2
from objects.conveyors.belt_segment import BeltSegment
from systems.conveyors.belt_system import BeltSystem


class _SplitterPreviewStub:
    """Minimal stand-in for a Splitter - just grid_pos/direction and
    _get_relative_dirs, enough for BeltSystem's duck-typed topology
    checks. Avoids instantiating a real Splitter (which loads its sprite
    from disk) purely to preview how it would affect nearby belts."""

    def __init__(self, grid_pos, direction):
        self.grid_pos = grid_pos
        self.direction = direction

    def _get_relative_dirs(self):
        dx, dy = float(self.direction.x), float(self.direction.y)
        return [
            Vector2(-dy, dx),
            Vector2(dx, dy),
            Vector2(dy, -dx),
        ]


class GhostMachineRenderer:
    """Draws the translucent placement preview for the currently selected machine class."""

    OVERLAY_COLORS = {
        "blocked": (255, 0, 0, 120),
        "no_space": (255, 165, 0, 120),
        "no_funds": (255, 255, 0, 120),
    }

    def __init__(self, world, player, camera, grid, screen, belt_ghost_preview_controller):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.screen = screen
        self.belt_ghost_preview_controller = belt_ghost_preview_controller

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

        cells = [
            (top_left_x + dx, top_left_y + dy)
            for dx in range(width)
            for dy in range(height)
        ]

        allow_replace = bool(py.key.get_mods() & py.KMOD_SHIFT)
        status = self._check_status(cells, selected_machine_class.BUILD_COST, allow_replace)

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

        if status in self.OVERLAY_COLORS:
            overlay = py.Surface(ghost.get_size(), py.SRCALPHA)
            overlay.fill(self.OVERLAY_COLORS[status])
            ghost.blit(overlay, (0, 0))

        if selected_machine_class.__name__ == "Splitter" and status != "blocked":
            self._draw_affected_belts((top_left_x, top_left_y), rotation_steps)

        # Draw at pixel position for camera
        pixel_x = top_left_x * self.grid.CELL_SIZE
        pixel_y = top_left_y * self.grid.CELL_SIZE
        self.screen.blit(ghost, (pixel_x - self.camera.x, pixel_y - self.camera.y))

    def _draw_affected_belts(self, grid_pos, rotation_steps):
        """Show how any existing neighboring belt's sprite would change if
        a splitter were actually placed here facing this way."""
        direction_map = [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]
        direction = direction_map[rotation_steps % 4]

        temp_splitter = _SplitterPreviewStub(grid_pos, direction)
        belt_system = self.belt_ghost_preview_controller.belt_system
        affected_segments = belt_system.resolve_splitter_preview_connections(temp_splitter)

        self.belt_ghost_preview_controller._draw_affected(affected_segments)

    def _check_status(self, cells, cost, allow_replace):
        """Returns "blocked", "no_space", "no_funds", or "ok" - the same
        rule MachineSystem.place_machine enforces: the player always
        blocks; a belt/machine tile blocks unless shift is held; and if
        not blocked, replacing whatever's there (if anything) has to
        actually fit and the net cost has to be affordable."""
        if any(self.world.is_blocked_by_player(cell) for cell in cells):
            return "blocked"
        if not allow_replace and any(self.world.is_cell_blocked(cell) for cell in cells):
            return "blocked"

        replaced_segments, replaced_machines = self.world.gather_occupants(cells)

        scratch = self.player.inventory.clone()
        if not BeltSystem.apply_refunds(scratch, replaced_segments, replaced_machines):
            return "no_space"
        if not scratch.try_remove_items(cost):
            return "no_funds"

        return "ok"
