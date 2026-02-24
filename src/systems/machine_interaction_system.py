import pygame as py

from objects.machines.producing_machine import ProducingMachine

class MachineInteractionSystem:
    def __init__(self, game):
        self.game = game

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return
        if just_placed_machine: return
        if self.game.build_mode is not None: return
        if self.game.machine_ui.open: return
        
        game = self.game

        mx, my = event.pos
        machine = game.world.get_machine_at_screen_pos(mx, my, game.camera)

        if isinstance(machine, ProducingMachine):
            game.machine_ui.open_for(machine)