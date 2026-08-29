# game.game
import pygame as py
from sys import exit

from game.initializer import Initializer, MIN_SCREEN_SIZE
from game.main_menu import MainMenu
from game import save_system
from objects.conveyors.belt_segment import update_all as update_all_belts

class Game:
    def __init__(self):
        py.init()
        py.key.start_text_input()
        py.key.set_repeat(500, 33)  # OS-style key repeat: 500ms delay, ~30/sec thereafter

        window_size = (max(1280, MIN_SCREEN_SIZE[0]), max(720, MIN_SCREEN_SIZE[1]))
        self.screen = py.display.set_mode(window_size, py.RESIZABLE)

        self.context = None
        self.state = "menu"  # "menu" | "playing"
        self.menu = MainMenu(get_screen_size=lambda: self.screen.get_size())

    def run(self):
        while True:
            events = py.event.get()

            for event in events:
                if event.type == py.QUIT:
                    py.quit()
                    exit()

                if event.type == py.VIDEORESIZE:
                    width = max(event.w, MIN_SCREEN_SIZE[0])
                    height = max(event.h, MIN_SCREEN_SIZE[1])
                    self.screen = py.display.set_mode((width, height), py.RESIZABLE)
                    if self.context is not None:
                        self.context.screen = self.screen
                        self._update_screen_size(width, height)
                        self.context.grid.update_screen_size(width, height)
                        self.context.build_mode_renderer.update_overlay_surfaces(width, height)

                if self.state == "playing" and event.type == py.MOUSEBUTTONUP and event.button == 1:
                    self.context.machine_system.just_placed_machine = False

            if self.state == "menu":
                self._run_menu_frame(events)
            else:
                self._run_game_frame(events)

            py.display.flip()

    def _run_menu_frame(self, events):
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

        self.menu.draw(self.screen)

    def _start_new_game(self, name):
        self.context = Initializer.init_game(screen=self.screen)
        save_system.new_game(self.context.world, self.context.player, self.context.camera, name)
        self.context.game_menu_bar.current_save_name = name
        self.state = "playing"

    def _start_loaded_game(self, name):
        self.context = Initializer.init_game(screen=self.screen)
        save_system.load_game(self.context.world, self.context.player, self.context.camera, self.context.belt_system, name)
        self.context.game_menu_bar.current_save_name = name
        self.state = "playing"

    def _run_game_frame(self, events):
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

        self.context.render_system.draw(self.context.screen)

        self.context.screen.blit(self.context.title_font_surface, (10, 10))
        self.context.screen.blit(self.context.font.render(f"Player position: x:{self.context.player.rect.centerx} y:{self.context.player.rect.centery}", True, "#000000"), (10, 35))
        self.context.screen.blit(self.context.font.render(f"FPS: {int(self.context.clock.get_fps())}", True, "#000000"), (10, 60))

    def _handle_event(self, event):
        if self.context.game_menu_bar.handle_event(event):
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

    def update(self, delta_time):
        self.context.player.update(self.context.world.machines, delta_time)
        self.context.camera.update(self.context.player)

        if self.context.hand_crafting_ui.open:
            self.context.hand_crafting_ui.update(delta_time)

        update_all_belts(self.context.world.belt_segments, self.context.world.belt_map, self.context.world.machine_map, delta_time)

        for machine in self.context.world.machines:
            machine.update(delta_time, self.context.world.belt_map, self.context.world.machine_map)

        self.context.build_system.update_hovered_delete_target()

        self._resolve_dirty_inventories(delta_time)

    def _resolve_dirty_inventories(self, delta_time):
        """Re-sorts any inventory that changed recently - belts feeding a
        storage building, or a player/storage click-transfer - once it's
        gone briefly untouched (Inventory.tick_dirty's debounce), rather
        than on every individual item movement. Producing machines aren't
        included: their input/output inventories are each a single-item
        1x1 slot, so there's nothing to sort."""
        self.context.player.inventory.tick_dirty(delta_time)

        for machine in self.context.world.machines:
            inventory = getattr(machine, "inventory", None)
            if inventory is not None:
                inventory.tick_dirty(delta_time)

    def _update_screen_size(self, width, height):
        self.context.camera.screen_width = width
        self.context.camera.screen_height = height
