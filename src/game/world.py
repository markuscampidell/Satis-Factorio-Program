# game.world
import pygame as py

class World:
    def __init__(self, player, cell_size):
        self.player = player
        self.cell_size = cell_size

        self.machines = []
        self.belt_segments = []

        self.machine_map = {}
        self.belt_map = {}



    def add_machine(self, machine):
        """Add a machine and map all its occupied cells."""
        self.machines.append(machine)
        for cell in machine.occupied_cells:
            self.machine_map[cell] = machine

    def remove_machine(self, machine):
        """Remove machine from world and lookup map."""
        if machine in self.machines:
            self.machines.remove(machine)
        for cell in getattr(machine, "occupied_cells", []):
            self.machine_map.pop(cell, None)

    def get_machine_at(self, grid_pos):
        """Return the machine at a given grid position, if any."""
        return self.machine_map.get(grid_pos)
    


    def add_belt_segment(self, seg):
        self.belt_segments.append(seg)
        self.belt_map[seg.grid_pos] = seg

    def remove_belt_segment(self, seg):
        if seg in self.belt_segments:
            self.belt_segments.remove(seg)
        self.belt_map.pop(seg.grid_pos, None)

    def get_belt_segment_at(self, world_x, world_y):
        tile = self.snap_to_tile(world_x, world_y)
        return self.belt_map.get(tile)

    def gather_occupants(self, cells):
        """Return all belt segments and machines found in the given cells.
        Machines that cover multiple cells are only included once."""
        segments = [self.belt_map[cell] for cell in cells if cell in self.belt_map]
        machines = list({
            id(machine): machine
            for cell in cells
            for machine in [self.machine_map.get(cell)]
            if machine is not None
        }.values())
        return segments, machines



    def snap_to_tile(self, x, y):
        """Convert pixel coordinates to tile indices (integers)."""
        return int(x // self.cell_size), int(y // self.cell_size)
    
    def is_cell_blocked(self, grid_pos):
        """Check if a cell is occupied by a machine or belt."""
        return grid_pos in self.machine_map or grid_pos in self.belt_map
    
    def is_blocked_by_player(self, grid_pos):
        """Check if the given grid cell is currently occupied by the player."""
        left = int(self.player.rect.left // self.cell_size)
        right = int((self.player.rect.right - 1) // self.cell_size)
        top = int(self.player.rect.top // self.cell_size)
        bottom = int((self.player.rect.bottom - 1) // self.cell_size)

        px, py = grid_pos

        # Return True if the grid_pos is inside the player's covered cells
        return left <= px <= right and top <= py <= bottom