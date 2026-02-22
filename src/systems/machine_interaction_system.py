import pygame as py

from objects.machines.producing_machine import ProducingMachine

class MachineInteractionSystem:
    def __init__(self, game):
        self.game = game

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return
        if just_placed_machine: return

        game = self.game

        # Don't block based on build_mode or other UIs — InputSystem already handles UI priority
        mx, my = event.pos
        machine = game.world.get_machine_at_screen_pos(mx, my, game.camera)

        if isinstance(machine, ProducingMachine):
            game.machine_ui.open_for(machine)