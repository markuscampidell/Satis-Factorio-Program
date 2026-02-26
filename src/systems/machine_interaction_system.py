import pygame as py

from objects.machines.producing_machine import ProducingMachine

class MachineInteractionSystem:
    def __init__(self, world, build_system, machine_ui, camera):
        self.world = world
        self.build_system = build_system
        self.machine_ui = machine_ui
        self.camera = camera

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return
        if just_placed_machine: return
        if self.build_system.build_mode is not None: return
        if self.machine_ui.open: return

        mx, my = event.pos
        machine = self.world.get_machine_at_screen_pos(mx, my, self.camera)

        if isinstance(machine, ProducingMachine):
            self.machine_ui.open_for(machine)