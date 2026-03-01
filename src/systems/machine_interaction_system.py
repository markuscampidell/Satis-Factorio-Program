# systems.machine_interaction_system
import pygame as py

from objects.machines.producing_machine import ProducingMachine

class MachineInteractionSystem:
    def __init__(self, world, build_system, machine_ui, camera, grid):
        self.world = world
        self.build_system = build_system
        self.machine_ui = machine_ui
        self.camera = camera
        self.grid = grid

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return
        if just_placed_machine:
            return
        if self.build_system.build_mode is not None:
            return
        if self.machine_ui.open:
            return

        mx, my = event.pos

        # Convert mouse to world coordinates
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        # Convert world coordinates to grid position
        grid_x, grid_y = self.grid.world_to_grid(world_x, world_y)

        # Check for a machine occupying that tile
        machine = self.world.get_machine_at((grid_x, grid_y))

        # Open UI if it's a ProducingMachine
        if machine and isinstance(machine, ProducingMachine):
            self.machine_ui.open_for(machine)