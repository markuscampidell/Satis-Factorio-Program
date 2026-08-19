# systems.rendering.world_renderer

class WorldRenderer:
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
        self._draw_grid(screen)

        self._draw_belt_segments(screen)
        self._draw_items(screen)
        self._draw_machines(screen)
        self.player.draw(screen, self.camera)
    
    def _draw_grid(self, screen):
        if self.build_system.build_mode is not None:
            self.grid.draw(screen, self.camera)

    def _draw_belt_segments(self, screen):
        cell_size = self.grid.CELL_SIZE

        camera_left = self.camera.x // cell_size
        camera_top = self.camera.y // cell_size
        camera_right = (self.camera.x + self.camera.screen_width) // cell_size + 1
        camera_bottom = (self.camera.y + self.camera.screen_height) // cell_size + 1

        for seg in self.world.belt_segments:
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
    def _draw_items(self, screen):
        for seg in self.world.belt_segments:
            if seg.item:
                self.item_renderer.draw_item(
                    screen,
                    self.camera,
                    seg.item,
                    seg.grid_pos,
                    seg.item_progress,
                    seg.current_incoming_direction or seg.direction
                )

        for machine in self.world.machines:
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