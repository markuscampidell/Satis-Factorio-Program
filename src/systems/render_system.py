# systems/render_system.py
import pygame as py
from objects.conveyors.conveyor_belt import BeltSegment

class RenderSystem:
    def __init__(self, game):
        self.game = game  # reference to the Game object
        self.image_cache = {}  # for cached belt images

    def draw(self, screen):
        game = self.game

        screen.fill("#987171")  # background

        """
        if game.build_mode is not None:
            game.grid.draw(screen, game.camera)
        """
        # Ghost previews
        if game.build_mode == "building" and game.selected_machine_class is not None:
            game.machine_placer.ghost_machine(game.selected_machine_class, game.build_mode, game.splitter_rotation_steps)
            game.belts.ghost_conveyor_belt(game.selected_machine_class, game.placing_belt, game.selected_belt_type)

        # Draw belts and items
        self._draw_belts(screen)
        self._draw_items_on_belts(screen)

        # Draw player
        game.player.draw(screen, game.camera)

        # Draw machines in camera view
        camera_rect = py.Rect(game.camera.x, game.camera.y, game.screen_width, game.screen_height)
        for machine in game.world.machines:
            if machine.rect.colliderect(camera_rect):
                machine.draw(screen, game.camera)

        # Draw UIs
        game.machine_ui.draw(screen)
        game.player_inventory_ui.draw(screen)

        # Highlight objects if deleting
        self._highlight_hovered_delete_target(screen)

        # Overlay for build/delete
        if game.build_mode == "building":
            screen.blit(game.overlay_build_place, (0, 0))
        elif game.build_mode == "deleting":
            screen.blit(game.overlay_delete, (0, 0))

        # Cursor
        self._draw_cursor(screen)

        # Text / debug info
        self._draw_texts(screen)
        
    def _draw_cursor(self, screen):
        game = self.game
        mx, my = py.mouse.get_pos()
        cursor_radius = 12
        cursor_surface = py.Surface((cursor_radius * 2, cursor_radius * 2), py.SRCALPHA)

        if game.build_mode == "building": 
            color = (255, 200, 50, 150)
        elif game.build_mode == "deleting": 
            color = (255, 100, 150, 120)
        else: 
            color = (255, 255, 255, 100)

        py.draw.circle(cursor_surface, color, (cursor_radius, cursor_radius), cursor_radius)
        py.draw.circle(cursor_surface, (0, 0, 0, 200), (cursor_radius, cursor_radius), cursor_radius, width=2)
        screen.blit(cursor_surface, (mx - cursor_radius, my - cursor_radius))

    def _draw_belts(self, screen):
        game = self.game
        camera_rect = py.Rect(game.camera.x, game.camera.y, game.screen_width, game.screen_height)

        for seg in game.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                incoming = seg.incoming_direction or seg.direction
                outgoing = seg.direction
                image = self._get_belt_segment_image(incoming, outgoing)
                if image:
                    screen.blit(image, (seg.rect.x - game.camera.x, seg.rect.y - game.camera.y))

    def _draw_items_on_belts(self, screen):
        game = self.game
        cell = game.grid.CELL_SIZE
        camera_rect = py.Rect(game.camera.x, game.camera.y, game.screen_width, game.screen_height)

        for seg in game.world.belt_segments:
            if seg.rect.colliderect(camera_rect):
                seg.draw_item(screen, game.camera, cell_size=cell)

    def _draw_texts(self, screen):
        game = self.game
        screen.blit(game.title_font_surface, (10, 10))
        screen.blit(game.font.render(f"Player position: x:{game.player.rect.centerx} y:{game.player.rect.centery}", True, "#000000"), (10, 50))
        screen.blit(game.font.render(f"FPS: {int(game.clock.get_fps())}", True, "#000000"), (10, 90))

    def _highlight_hovered_delete_target(self, screen):
        game = self.game
        if game.build_mode != "deleting" or game.hovered_delete_target is None:
            return

        alpha = 100
        color = (255, 0, 0)
        shift_held = py.key.get_mods() & py.KMOD_SHIFT

        if isinstance(game.hovered_delete_target, BeltSegment) and shift_held:
            segments_to_highlight = game.belts.get_connected_belt_segments(game.hovered_delete_target)
        else:
            segments_to_highlight = [game.hovered_delete_target]

        for obj in segments_to_highlight:
            if hasattr(obj, "rect"):
                rect = obj.rect
                overlay = py.Surface((rect.width, rect.height), py.SRCALPHA)
                overlay.fill((*color, alpha))
                screen.blit(overlay, (rect.x - game.camera.x, rect.y - game.camera.y))

    def _get_belt_segment_image(self, incoming, outgoing):
        game = self.game
        key = (incoming.x, incoming.y, outgoing.x, outgoing.y)
        if key not in self.image_cache:
            if incoming.x == outgoing.x and incoming.y == outgoing.y:
                image = game.belt_sprite_manager.get_straight(outgoing)
            else:
                image = game.belt_sprite_manager.get_curve(incoming, outgoing)
            self.image_cache[key] = image
        return self.image_cache[key]