# systems/render_system.py
import pygame as py
from objects.conveyors.belt_segment import BeltSegment

class RenderSystem:
    def __init__(self, world, player, camera, grid, build_system, belt_sprite_manager, machine_ui, player_invenotry_ui, hand_crafting_ui, machine_system, ghost_placer, belts):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.build_system = build_system
        self.belt_sprite_manager = belt_sprite_manager
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_invenotry_ui
        self.hand_crafting_ui = hand_crafting_ui
        self.machine_system = machine_system
        self.ghost_placer = ghost_placer
        self.belts = belts

        self.image_cache = {}

    def draw(self, screen):
        screen.fill("#987171")  # background

        
        if self.build_system.build_mode is not None:
            self.grid.draw(screen, self.camera)
        
        # Ghost previews
        # Ghost previews
        if self.build_system.build_mode == "building" and self.build_system.selected_machine_class is not None:
            # Machines
            self.machine_system.ghost_machine(
                self.build_system.selected_machine_class,
                self.build_system.build_mode,
                self.machine_system.splitter_rotation_steps   # from MachineSystem
            )
            # Belts
            self.ghost_placer.draw_ghost(
                self.build_system.selected_machine_class,
                self.belts.placing_belt,                # from BeltSystem
                self.belts.selected_belt_type          # from BeltSystem
            )

        # Draw belts and items
        self._draw_belts(screen)
        self._draw_items_on_belts(screen)

        # Draw player
        self.player.draw(screen, self.camera)

        # Draw machines in camera view
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)
        for machine in self.world.machines:
            if machine.rect.colliderect(camera_rect):
                machine.draw(screen, self.camera)

        # Draw UIs
        self.machine_ui.draw(screen)
        self.player_inventory_ui.draw(screen)
        self.hand_crafting_ui.draw(screen)

        # Highlight objects if deleting
        self._highlight_hovered_delete_target(screen)

        """
        # Overlay for build/delete
        if self.build_system.build_mode == "building":
            screen.blit(self.build_system.overlay_build_place, (0, 0))
        elif self.build_system.build_mode == "deleting":
            screen.blit(self.build_system.overlay_delete, (0, 0))
        """
            
        # Cursor
        self._draw_cursor(screen)

        # Text / debug info
        self._draw_texts(screen)
        
    def _draw_cursor(self, screen):
        mx, my = py.mouse.get_pos()
        cursor_radius = 12
        cursor_surface = py.Surface((cursor_radius * 2, cursor_radius * 2), py.SRCALPHA)

        if self.build_system.build_mode == "building": 
            color = (255, 200, 50, 150)
        elif self.build_system.build_mode == "deleting": 
            color = (255, 100, 150, 120)
        else: 
            color = (255, 255, 255, 100)

        py.draw.circle(cursor_surface, color, (cursor_radius, cursor_radius), cursor_radius)
        py.draw.circle(cursor_surface, (0, 0, 0, 200), (cursor_radius, cursor_radius), cursor_radius, width=2)
        screen.blit(cursor_surface, (mx - cursor_radius, my - cursor_radius))

    def _draw_belts(self, screen):
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        for seg in self.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                incoming = seg.incoming_direction or seg.direction
                outgoing = seg.direction
                image = self._get_belt_segment_image(incoming, outgoing)
                if image:
                    screen.blit(image, (seg.rect.x - self.camera.x, seg.rect.y - self.camera.y))

    def _draw_items_on_belts(self, screen):
        cell = self.grid.CELL_SIZE
        camera_rect = py.Rect(self.camera.x, self.camera.y, self.camera.screen_width, self.camera.screen_height)

        for seg in self.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                seg.draw_item(screen, self.camera, cell_size=cell)

    def _draw_texts(self, screen):
        """ i need to make a file debug_overlay
        screen.blit(self.title_font_surface, (10, 10))
        screen.blit(self.font.render(f"Player position: x:{self.player.rect.centerx} y:{self.player.rect.centery}", True, "#000000"), (10, 35))
        screen.blit(self.font.render(f"FPS: {int(self.clock.get_fps())}", True, "#000000"), (10, 60))
        """
        
    def _highlight_hovered_delete_target(self, screen):
        if self.build_system.build_mode != "deleting" or self.build_system.hovered_delete_target is None: return

        alpha = 100
        color = (255, 0, 0)
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        if isinstance(self.build_system.hovered_delete_target, BeltSegment) and shift_held:
            segments_to_highlight = self.belts.get_connected_belt_segments(self.build_system.hovered_delete_target)
        else:
            segments_to_highlight = [self.build_system.hovered_delete_target]

        for obj in segments_to_highlight:
            if hasattr(obj, "rect"):
                rect = obj.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill((*color, alpha))
                screen.blit(overlay, (rect.x - self.camera.x, rect.y - self.camera.y))

    def _get_belt_segment_image(self, incoming, outgoing):
        key = (incoming.x, incoming.y, outgoing.x, outgoing.y)
        if key not in self.image_cache:
            if incoming.x == outgoing.x and incoming.y == outgoing.y:
                image = self.belt_sprite_manager.get_straight(outgoing)
            else:
                image = self.belt_sprite_manager.get_curve(incoming, outgoing)
            self.image_cache[key] = image
        return self.image_cache[key]