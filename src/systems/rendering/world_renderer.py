# systems.rendering.world_renderer
import pygame as py

class WorldRenderer:
    def __init__(self, world, camera, player, belt_sprite_manager, build_system, grid):
        self.world = world
        self.camera = camera
        self.player = player
        self.belt_sprite_manager = belt_sprite_manager
        self.build_system = build_system
        self.grid = grid

        self.image_cache = {}
    
    def draw(self, screen):
        self._draw_grid(screen)

        self._draw_belt_segments(screen)
        self._draw_items_on_belt_segments(screen)
        self._draw_machines(screen)
        self.player.draw(screen, self.camera)
    
    def _draw_grid(self, screen):
        if self.build_system.build_mode is not None:
            self.grid.draw(screen, self.camera)

    def _draw_belt_segments(self, screen):
        camera_left = self.camera.x // self.grid.CELL_SIZE
        camera_top = self.camera.y // self.grid.CELL_SIZE
        camera_right = (self.camera.x + self.camera.screen_width) // self.grid.CELL_SIZE + 1
        camera_bottom = (self.camera.y + self.camera.screen_height) // self.grid.CELL_SIZE + 1

        for seg in self.world.belt_segments:
            gx, gy = seg.grid_pos  # assume you store belt grid positions
            if camera_left <= gx < camera_right and camera_top <= gy < camera_bottom:
                incoming = seg.incoming_direction or seg.direction
                outgoing = seg.direction
                image = self._get_belt_segment_image(incoming, outgoing)
                screen.blit(image, (gx*self.grid.CELL_SIZE - self.camera.x, gy*self.grid.CELL_SIZE - self.camera.y))

    def _draw_items_on_belt_segments(self, screen):
        cell_size = self.grid.CELL_SIZE
        camera_left = self.camera.x // cell_size
        camera_top = self.camera.y // cell_size
        camera_right = (self.camera.x + self.camera.screen_width) // cell_size + 1
        camera_bottom = (self.camera.y + self.camera.screen_height) // cell_size + 1

        for seg in self.world.belt_segments:
            gx, gy = seg.grid_pos
            if camera_left <= gx < camera_right and camera_top <= gy < camera_bottom:
                seg.draw_item(screen, self.camera)
    
    def _get_belt_segment_image(self, incoming, outgoing):
        key = (incoming.x, incoming.y, outgoing.x, outgoing.y)
        if key not in self.image_cache:
            if incoming.x == outgoing.x and incoming.y == outgoing.y:
                image = self.belt_sprite_manager.get_straight(outgoing)
            else:
                image = self.belt_sprite_manager.get_curve(incoming, outgoing)
            self.image_cache[key] = image
        return self.image_cache[key]
    
    def _draw_machines(self, screen):
        camera_left = self.camera.x // self.grid.CELL_SIZE
        camera_top = self.camera.y // self.grid.CELL_SIZE
        camera_right = (self.camera.x + self.camera.screen_width) // self.grid.CELL_SIZE + 1
        camera_bottom = (self.camera.y + self.camera.screen_height) // self.grid.CELL_SIZE + 1

        for machine in self.world.machines:
            # Check if any of the machine's tiles are inside camera view
            for gx, gy in machine.occupied_cells:
                if camera_left <= gx < camera_right and camera_top <= gy < camera_bottom:
                    machine.draw(screen, self.camera)
                    break  # only draw once