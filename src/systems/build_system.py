# systems.build_system
import pygame as py

from objects.machines.splitter import Splitter
from objects.conveyors.belt_segment import BeltSegment
from objects.machines.smelter import Smelter
from core.vector2 import Vector2

class BuildSystem:
    def __init__(self, world, player, camera, grid, belt_system, machine_system, machine_ui, player_inventory_ui):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.belt_system = belt_system
        self.machine_system = machine_system
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui

        # Build state
        self.build_mode = None
        self.selected_machine_class = Smelter
        self.hovered_delete_target = None

    def handle_placement(self, event):
        if self.player_inventory_ui.open or self.machine_ui.open: return
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return

        mx, my = event.pos
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        # Delete mode
        if self.build_mode == "deleting":
            self.machine_system.delete_machine(mx, my)
            self.belt_system.delete_belt(
                mx, my,
                delete_whole=bool(py.key.get_mods() & py.KMOD_SHIFT),
                camera_x=self.camera.x,
                camera_y=self.camera.y,
                player_inventory=self.player.inventory
            )
            self.update_all_splitters_outputs()
            return

        # Belt placement
        if self.build_mode == "building" and self.selected_machine_class is BeltSegment:
            if not self.belt_system.placing_belt:
                if self._mouse_over_ui(mx, my):
                    return
                self.belt_system.placing_belt = True
                # FIX: store tile indices, not pixels
                self.belt_system.beltX1, self.belt_system.beltY1 = self.world.snap_to_tile(world_x, world_y)
                return
            else:
                if self._mouse_over_ui(mx, my):
                    return
                self.belt_system.place_belt(world_x, world_y, self.belt_system.selected_belt_type)
                self.update_all_splitters_outputs()
                self.belt_system.placing_belt = False
                return

        # Machine placement
        if self.build_mode == "building" and self.selected_machine_class is not None:
            self.machine_system.place_machine(self.selected_machine_class)
            if hasattr(self, 'preview_splitter'):
                self.preview_splitter = None

    def update_all_splitters_outputs(self):
        cell = self.grid.CELL_SIZE
        for machine in self.world.machines:
            if isinstance(machine, Splitter):
                output_belts = []
                for direction in machine._get_relative_dirs():
                    next_rect = machine.rect.move(int(direction.x * cell), int(direction.y * cell))
                    seg = self.world.belt_map.get((next_rect.x, next_rect.y))
                    output_belts.append(seg)
                machine.output_belts = [b for b in output_belts if b]
                if machine.output_belts:
                    machine.current_output_index %= len(machine.output_belts)
                else:
                    machine.current_output_index = 0

    def update_hovered_delete_target(self):
        if self.build_mode != "deleting":
            self.hovered_delete_target = None
            return

        # Mouse grid coordinates
        mx, my = py.mouse.get_pos()
        grid_x = (mx + self.camera.x) // self.grid.CELL_SIZE
        grid_y = (my + self.camera.y) // self.grid.CELL_SIZE

        # Check machines by tile
        self.hovered_delete_target = None
        for machine in self.world.machines:
            for cell in getattr(machine, "occupied_cells", []):
                if cell == (grid_x, grid_y):
                    self.hovered_delete_target = machine
                    return

        # Check belts by tile
        seg = self.world.belt_map.get((grid_x, grid_y))
        if seg:
            self.hovered_delete_target = seg

    def _mouse_over_ui(self, mx, my):
        return ((self.machine_ui.open and self.machine_ui.rect.collidepoint(mx, my)) or
                (self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my)))
    
    def exit_build_mode(self):
        self.build_mode = None
        self.belt_system.placing_belt = False

    def enter_build_mode(self):
        self.build_mode = "building"
        self.belt_system.placing_belt = False

    def enter_delete_mode(self):
        self.build_mode = "deleting"
        self.belt_system.placing_belt = False

    def rotate_selected(self):
        if self.selected_machine_class is Splitter:
            self.machine_system.splitter_rotation_steps = (self.machine_system.splitter_rotation_steps + 1) % 4
        elif self.selected_machine_class is BeltSegment:
            x, y = self.belt_system.belt_placement_direction.x, self.belt_system.belt_placement_direction.y
            self.belt_system.belt_placement_direction = Vector2(-y, x)

    def toggle_build_mode(self):
        if self.build_mode == "building":
            self.build_mode = None
        else:
            self.build_mode = "building"
            self.belt_system.placing_belt = False

    def toggle_delete_mode(self):
        if self.build_mode == "deleting":
            self.build_mode = None
        else:
            self.build_mode = "deleting"
    
    def select_machine(self, machine_class):
        self.selected_machine_class = machine_class
        self.machine_system.splitter_rotation_steps = 0
        self.belt_system.placing_belt = False

        if self.build_mode != "building":
            self.build_mode = "building"
    
    def reset_build_state(self):
        self.build_mode = None
        self.selected_machine_class = Smelter
        self.belt_system.placing_belt = False
        self.reset_rotation()
        self.belt_system.belt_first_axis_horizontal = True
    
    def reset_rotation(self):
        self.belt_system.belt_placement_direction = Vector2(1, 0)
        self.machine_system.splitter_rotation_steps = 0