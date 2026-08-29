# systems.machine_interaction_system
import pygame as py

from objects.machines.producing_machine import ProducingMachine
from objects.machines.storage import Storage

class MachineInteractionSystem:
    def __init__(self, world, build_system, machine_ui, camera, hand_crafting_ui, storage_ui, player_inventory_ui):
        self.world = world
        self.build_system = build_system
        self.machine_ui = machine_ui
        self.camera = camera
        self.hand_crafting_ui = hand_crafting_ui
        self.storage_ui = storage_ui
        self.player_inventory_ui = player_inventory_ui

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return
        if just_placed_machine:
            return
        if self.build_system.build_mode is not None:
            return
        if self.machine_ui.open or self.storage_ui.open:
            return

        mx, my = event.pos

        # Convert mouse to world coordinates
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        # Convert world coordinates to grid position
        grid_x, grid_y = self.world.snap_to_tile(world_x, world_y)

        # Check for a machine occupying that tile
        machine = self.world.get_machine_at((grid_x, grid_y))

        # Open the matching UI depending on what kind of machine this is
        if machine and isinstance(machine, ProducingMachine):
            self.hand_crafting_ui.close()
            self.machine_ui.open_for(machine)
            self.player_inventory_ui.open = True
        elif machine and isinstance(machine, Storage):
            self.hand_crafting_ui.close()
            self.storage_ui.open_for(machine)
            self.player_inventory_ui.open = True