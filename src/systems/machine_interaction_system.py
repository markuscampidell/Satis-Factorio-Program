import pygame as py

from objects.machines.producing_machine import ProducingMachine

class MachineInteractionSystem:
    def __init__(self, game):
        self.game = game

    def handle_click(self, event):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return

        game = self.game
        if game.machine_ui.open or game.player_inventory_ui.open or game.just_placed_machine or game.build_mode is not None:
            return

        mx, my = event.pos
        machine = game.world.get_machine_at_screen_pos(mx, my, game.camera)

        if isinstance(machine, ProducingMachine):
            game.machine_ui.open_for(machine)