# game.world
class World:
    def __init__(self, player, cell_size):
        self.player = player
        self.cell_size = cell_size

        self.machines = []
        self.belt_segments = []

        self.machine_map = {}
        self.belt_map = {}



    def snap_to_grid(self, x, y):
        cell = self.cell_size
        return (x // cell * cell, y // cell * cell)



    def add_machine(self, machine):
        self.machines.append(machine)

        machine._occupied_cells = []

        for x in range(machine.rect.left, machine.rect.right, self.cell_size):
            for y in range(machine.rect.top, machine.rect.bottom, self.cell_size):
                pos = (x, y)
                self.machine_map[pos] = machine
                machine._occupied_cells.append(pos)

    def remove_machine(self, machine):
        if machine in self.machines:
            self.machines.remove(machine)

        for pos in getattr(machine, "_occupied_cells", []):
            self.machine_map.pop(pos, None)

    def get_machine_at_screen_pos(self, mx, my, camera):
        world_x = mx + camera.x
        world_y = my + camera.y

        snapped = self.snap_to_grid(world_x, world_y)
        return self.machine_map.get(snapped)



    def add_belt_segment(self, seg):
        self.belt_segments.append(seg)
        self.belt_map[seg.rect.topleft] = seg

    def remove_belt_segment(self, seg):
        if seg in self.belt_segments:
            self.belt_segments.remove(seg)
        self.belt_map.pop(seg.rect.topleft, None)

    def get_belt_segment_at(self, world_x, world_y):
        snapped = self.snap_to_grid(world_x, world_y)
        return self.belt_map.get(snapped)



    def is_rect_blocked(self, rect):
        pos = rect.topleft

        if pos in self.machine_map:
            return True

        if pos in self.belt_map:
            return True

        if self.player.rect.colliderect(rect):
            return True

        return False