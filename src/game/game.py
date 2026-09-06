# game.game
import pygame as py
from sys import exit

from game.initializer import MIN_SCREEN_SIZE
from game.main_menu import MainMenu
from game.game_orchestrator import GameOrchestrator


class Game:
    """Starts pygame and runs the main loop. Shows either the main menu or
    the actual running game, depending on what state things are in."""

    def __init__(self):
        py.init()
        py.key.start_text_input()
        py.key.set_repeat(500, 33)  # OS-style key repeat: 500ms delay, ~30/sec thereafter

        window_size = (max(1280, MIN_SCREEN_SIZE[0]), max(720, MIN_SCREEN_SIZE[1]))
        self.screen = py.display.set_mode(window_size, py.RESIZABLE)

        self.menu = MainMenu(get_screen_size=lambda: self.screen.get_size())

        self.game_orchestrator = GameOrchestrator(screen=self.screen, menu=self.menu)

    def run(self):
        """The main loop. Keeps reading input and drawing frames forever,
        handing off to the menu or the actual game depending on which one
        is currently active."""
        while True:
            events = py.event.get()

            for event in events:
                if event.type == py.QUIT:
                    py.quit()
                    exit()

                self.game_orchestrator.video_resize(event)

                self.game_orchestrator._update_just_placed_machine(event)

            if self.game_orchestrator.state == "menu":
                self.game_orchestrator._run_menu_frame(events)
            else:
                self.game_orchestrator._run_game_frame(events)

            py.display.flip()