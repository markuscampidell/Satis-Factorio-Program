# game.save_load_orchestrator.py
import pygame as py

from game.initializer import Initializer, MIN_SCREEN_SIZE
from game import save_system

from objects.conveyors.belt_segment import update_all as update_all_belts

class GameOrchestrator:
    """Switches between the main menu and the actual running game, and
    runs whichever one is currently active, one frame at a time."""

    def __init__(self, screen, menu):
        self.screen = screen
        self.menu = menu
        self.context = None
        self.state = "menu"
        # The "playing" state gets its delta_time from context.clock
        # (created per-game in Initializer), but the main menu has no
        # context yet - it needs its own clock so its TextInputs' cursor
        # blink measures real elapsed time instead of assuming a fixed
        # 1/60s per frame, which used to be wrong here specifically: this
        # loop iterates unthrottled while the "playing" loop is capped to
        # 60fps via context.clock.tick(60), so the same hardcoded "1/60"
        # produced a visibly faster blink in the menu than in-game.
        self.menu_clock = py.time.Clock()

    def update(self, delta_time):
            """Runs one tick of the actual game world: moves the player,
            follows them with the camera, and advances belts and
            machines."""
            self.context.player.update(self.context.world.machines)
            self.context.camera.update(self.context.player)
    
            if self.context.hand_crafting_ui.open:
                self.context.hand_crafting_ui.update(delta_time)
    
            update_all_belts(self.context.world.belt_segments, self.context.world.belt_map, self.context.world.machine_map, delta_time)
    
            for machine in self.context.world.machines:
                machine.update(delta_time, self.context.world.belt_map, self.context.world.machine_map)
    
            self.context.build_system.update_hovered_delete_target()
            self.context.machine_interaction_system.update_hover()

    def _update_screen_size(self, width, height):
        self.context.camera.screen_width = width
        self.context.camera.screen_height = height

    def _handle_event(self, event):
            """Passes one input event along to whichever part of the game
            should react to it, checking the menus and popups first before
            letting it reach the actual game world."""
            if self.context.game_menu_bar.handle_event(event):
                return
    
            if self.context.build_hotbar.handle_event(event):
                return
    
            # ESC opens the Game Menu, but only when not mid-build/delete and no
            # other UI (inventory/machine/hand-crafting) is open - in those
            # cases ESC keeps its existing job of canceling/closing instead
            # (handled below by input_system.handle_keys).
            if (event.type == py.KEYDOWN and event.key == py.K_ESCAPE
                    and self.context.build_system.build_mode is None
                    and not self.context.player_inventory_ui.open
                    and not self.context.machine_ui.open
                    and not self.context.hand_crafting_ui.open
                    and not self.context.storage_ui.open
                    and not self.context.belt_filter_ui.open
                    and not self.context.splitter_filter_ui.open):
                self.context.game_menu_bar.game_menu_open = True
                return
    
            self.context.input_system.handle_keys(event)
            self.context.input_system.handle_mouse(event)
    
            self.context.build_system.handle_placement(event)
    
            self.context.machine_ui.handle_event(event, self.context.machine_system.just_placed_machine, self.context.build_system.build_mode == "building",)
            self.context.storage_ui.handle_event(event, self.context.machine_system.just_placed_machine, self.context.build_system.build_mode == "building")
            self.context.belt_filter_ui.handle_event(event, self.context.machine_system.just_placed_machine, self.context.build_system.build_mode == "building")
            self.context.splitter_filter_ui.handle_event(event, self.context.machine_system.just_placed_machine, self.context.build_system.build_mode == "building")
            self.context.player_inventory_ui.handle_event(event, self.context.machine_ui, self.context.storage_ui)
    
            self.context.machine_interaction_system.handle_click(event, self.context.machine_system.just_placed_machine)
            self.context.machine_interaction_system.handle_pick_key(event)

    def start_new_game(self, name):
        """Builds a brand new game world and saves it under this name
        right away."""
        context = Initializer.init_game(screen=self.screen)

        save_system.new_game(
            context.world,
            context.player,
            context.camera,
            name
        )

        context.game_menu_bar.current_save_name = name
        return context

    def load_game(self, name):
        """Builds a fresh game world, then fills it in with whatever was
        saved under this name."""
        context = Initializer.init_game(screen=self.screen)

        save_system.load_game(
            context.world,
            context.player,
            context.camera,
            context.belt_system,
            name
        )

        context.game_menu_bar.current_save_name = name
        return context

    def save_game(self, context):
        """Writes the current game to disk, under whatever name it's
        already saved as."""
        save_system.save_game(
            context.world,
            context.player,
            context.camera,
            context.game_menu_bar.current_save_name
        )


    def _run_menu_frame(self, events):
            """Runs one frame of the main menu: handles clicks/typing, then
            actually starts or loads a game if the menu asked for one."""
            delta_time = self.menu_clock.tick(60) / 1000

            for event in events:
                action = self.menu.handle_event(event)
                if action is None:
                    continue

                if action[0] == "start_new_game":
                    self._start_new_game(action[1])
                elif action[0] == "load_game":
                    self._start_loaded_game(action[1])
                elif action[0] == "quit":
                    py.quit()
                    exit()

            self.menu.draw(self.screen, delta_time)


    def _run_game_frame(self, events):
            """Runs one frame of the actual game: handles input, updates
            everything, then draws it - or leaves back to the menu if the
            player asked to."""
            for event in events:
                self._handle_event(event)
    
            if self.context.game_menu_bar.return_to_menu_requested:
                if self.context.game_menu_bar.save_before_return:
                    save_system.save_game(self.context.world, self.context.player, self.context.camera, self.context.game_menu_bar.current_save_name)
                self.context = None
                self.state = "menu"
                self.menu.refresh_save_list()
                return
    
            delta_time = self.context.clock.tick(60) / 1000
            if not self.context.game_menu_bar.game_menu_open:
                self.update(delta_time)

            self.context.render_system.draw(self.context.screen, delta_time)
    
            self.context.screen.blit(self.context.title_font_surface, (10, 10))
            self.context.screen.blit(self.context.font.render(f"Player position: x:{self.context.player.rect.centerx} y:{self.context.player.rect.centery}", True, "#000000"), (10, 35))
            self.context.screen.blit(self.context.font.render(f"FPS: {int(self.context.clock.get_fps())}", True, "#000000"), (10, 60))


    def _start_new_game(self, name):
        self.context = self.start_new_game(name)
        self.state = "playing"
    
    def _start_loaded_game(self, name):
        self.context = self.load_game(name)
        self.state = "playing"

    def video_resize(self, event=None):
         """Resizes the game window and tells the camera/grid/UI about the
         new size, so everything still lines up correctly."""
         if event.type == py.VIDEORESIZE:
            width = max(event.w, MIN_SCREEN_SIZE[0])
            height = max(event.h, MIN_SCREEN_SIZE[1])
            self.screen = py.display.set_mode((width, height), py.RESIZABLE)
            if self.context is not None:
                self.context.screen = self.screen
                self._update_screen_size(width, height)
                self.context.grid.update_screen_size(width, height)
                self.context.build_mode_renderer.update_overlay_surfaces(width, height)

    def _update_just_placed_machine(self, event):
        """Clears the "just placed a machine" flag once the mouse button
        comes back up, so that same click can't also be read as clicking
        on the machine to open its panel."""
        if self.state == "playing" and event.type == py.MOUSEBUTTONUP and event.button == 1:
            if self.context is not None:
                self.context.machine_system.just_placed_machine = False