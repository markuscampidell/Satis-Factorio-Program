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
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        for seg in self.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                incoming = seg.incoming_direction or seg.direction
                outgoing = seg.direction
                image = self._get_belt_segment_image(incoming, outgoing)
                if image:
                    screen.blit(image, (seg.rect.x - self.camera.x, seg.rect.y - self.camera.y))

    def _draw_items_on_belt_segments(self, screen):
        cell = 32 # self.grid.CELL_SIZE
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        for seg in self.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                seg.draw_item(screen, self.camera, cell_size=cell)
    
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
        camera_rect = py.Rect(self.camera.x, self.camera.y,
                              self.camera.screen_width, self.camera.screen_height)
        
        for machine in self.world.machines:
            if machine.rect.colliderect(camera_rect):
                machine.draw(screen, self.camera)