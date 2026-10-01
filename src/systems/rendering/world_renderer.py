# systems.rendering.world_renderer
import pygame as py

from objects.filter_badge import draw_filter_badge
from game.chunk import CHUNK_SIZE
from game.terrain import ORE_TILE_TYPES
from constants.itemdata import get_item_by_id

GROUND_COLOR = (110, 88, 60)  # placeholder flat ground color


class WorldRenderer:
    """Draws the actual game world - the ground, grid, belts, items,
    machines, and the player - in the right order so nothing gets covered
    up wrong."""

    def __init__(self, world, camera, player, belt_sprite_manager, item_renderer, build_system, grid):
        self.world = world
        self.camera = camera
        self.player = player
        self.belt_sprite_manager = belt_sprite_manager
        self.item_renderer = item_renderer
        self.build_system = build_system
        self.grid = grid

        self.image_cache = {}

    def draw(self, screen):
        self._draw_terrain(screen)
        self._draw_grid(screen)

        self._draw_belt_segments(screen)
        self._draw_items(screen)
        self._draw_machines(screen)
        self.player.draw(screen, self.camera)

    def _draw_terrain(self, screen):
        """Draws the generated ground - grass, with a small icon of
        whichever ore an ore tile would let a Miner produce - under
        everything else. One cached Surface per chunk (see
        _build_terrain_surface), so this is just a cheap blit per visible
        chunk every frame, not a per-tile draw."""
        cell_size = self.grid.CELL_SIZE
        camera_left, camera_top, camera_right, camera_bottom = self.camera.visible_tile_rect(cell_size)

        for chunk in self.world.ensure_chunks_in_tile_rect(camera_left, camera_top, camera_right, camera_bottom):
            if chunk.terrain_surface is None:
                chunk.terrain_surface = self._build_terrain_surface(chunk, cell_size)

            pixel_x = chunk.cx * CHUNK_SIZE * cell_size - self.camera.x
            pixel_y = chunk.cy * CHUNK_SIZE * cell_size - self.camera.y
            screen.blit(chunk.terrain_surface, (pixel_x, pixel_y))

    def _build_terrain_surface(self, chunk, cell_size):
        """Built once per chunk and cached on it: a flat ground color, with
        a small icon of the matching ore item (reusing its existing
        sprite - same idiom as Storage's own "what's inside" icon) centered
        on each ore tile. No new ground-tile art needed."""
        size = CHUNK_SIZE * cell_size
        surface = py.Surface((size, size))
        surface.fill(GROUND_COLOR)

        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                item_id = ORE_TILE_TYPES.get(chunk.tiles[ly][lx])
                if not item_id:
                    continue

                item = get_item_by_id(item_id)
                if not item or not item.sprite:
                    continue

                icon = item.get_scaled_sprite(int(cell_size * 0.7))
                screen_x = lx * cell_size + (cell_size - icon.get_width()) // 2
                screen_y = ly * cell_size + (cell_size - icon.get_height()) // 2
                surface.blit(icon, (screen_x, screen_y))

        return surface

    def _draw_grid(self, screen):
        if self.build_system.build_mode is not None:
            self.grid.draw(screen, self.camera)
            self.grid.draw_chunk_borders(screen, self.camera)

    def _draw_belt_segments(self, screen):
        """Draws every belt tile that's actually on screen, plus a small
        badge on the ones with an active filter."""
        cell_size = self.grid.CELL_SIZE
        camera_left, camera_top, camera_right, camera_bottom = self.camera.visible_tile_rect(cell_size)

        for seg in self.world.belt_segments_in_tile_rect(camera_left, camera_top, camera_right, camera_bottom):
            gx, gy = seg.grid_pos

            if camera_left <= gx < camera_right and camera_top <= gy < camera_bottom:
                incoming_directions = seg.incoming_directions or [seg.direction]

                image = self.belt_sprite_manager.get_sprite(incoming_directions, seg.direction)

                screen.blit(
                    image,
                    (
                        gx * cell_size - self.camera.x,
                        gy * cell_size - self.camera.y
                    )
                )

                if seg.filter.enabled:
                    corner_x = gx * cell_size - self.camera.x + cell_size - 8
                    corner_y = gy * cell_size - self.camera.y + 8
                    draw_filter_badge(screen, (corner_x, corner_y), size=10)

    def _draw_items(self, screen):
        """Draws every item currently traveling on a belt or animating
        into a machine, restricted to the belts/machines actually near the
        camera."""
        cell_size = self.grid.CELL_SIZE
        camera_left, camera_top, camera_right, camera_bottom = self.camera.visible_tile_rect(cell_size)

        for seg in self.world.belt_segments_in_tile_rect(camera_left, camera_top, camera_right, camera_bottom):
            if seg.item:
                self.item_renderer.draw_item(
                    screen,
                    self.camera,
                    seg.item,
                    seg.grid_pos,
                    seg.item_progress,
                    seg.current_incoming_direction or seg.direction
                )

        for machine in self.world.machines_in_tile_rect(camera_left, camera_top, camera_right, camera_bottom):
            if hasattr(machine, "current_item") and machine.current_item:
                self.item_renderer.draw_item(
                    screen,
                    self.camera,
                    machine.current_item,
                    machine.grid_pos,
                    machine.item_progress,
                    machine.current_incoming_direction or machine.direction
                )

            input_animator = getattr(machine, "input_animator", None)
            for anim in (input_animator.animations if input_animator else []):
                self.item_renderer.draw_item_lerp(
                    screen,
                    self.camera,
                    anim["item"],
                    anim["start"],
                    anim["end"],
                    min(anim["progress"], 1.0)
                )
    
    def _draw_machines(self, screen):
        """Draws every machine that's actually on screen, skipping the
        ones the camera can't currently see."""
        camera_left, camera_top, camera_right, camera_bottom = self.camera.visible_tile_rect(self.grid.CELL_SIZE)

        for machine in self.world.machines_in_tile_rect(camera_left, camera_top, camera_right, camera_bottom):
            # Check if any of the machine's tiles are inside camera view
            for gx, gy in machine.occupied_cells:
                if camera_left <= gx < camera_right and camera_top <= gy < camera_bottom:
                    machine.draw(screen, self.camera)
                    break  # only draw once