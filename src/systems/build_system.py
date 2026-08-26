# systems.build_system
import pygame as py

from objects.machines.splitter import Splitter
from objects.conveyors.belt_segment import BeltSegment
from objects.machines.smelter import Smelter
from core.vector2 import Vector2

class BuildSystem:
    def __init__(self, world, player, camera, grid, belt_system, machine_system, machine_ui, player_inventory_ui, storage_ui):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.belt_system = belt_system
        self.machine_system = machine_system
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui
        self.storage_ui = storage_ui

        # Build state
        self.build_mode = None
        self.selected_machine_class = Smelter
        self.hovered_delete_target = None

    def handle_placement(self, event):
        if self.player_inventory_ui.open or self.machine_ui.open or self.storage_ui.open: return
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
                camera_y=self.camera.y)
            self.belt_system.update_belt_incoming_directions()
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
                self.belt_system.placing_belt = False
                return

        # Machine placement
        if self.build_mode == "building" and self.selected_machine_class is not None:
            self.machine_system.place_machine(self.selected_machine_class)
            self.belt_system.update_belt_incoming_directions()
            if hasattr(self, 'preview_splitter'):
                self.preview_splitter = None

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
                (self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my)) or
                (self.storage_ui.open and self.storage_ui.rect.collidepoint(mx, my)))
    
    def exit_build_mode(self):
        self.build_mode = None
        self.belt_system.placing_belt = False

    def enter_build_mode(self):
        self.build_mode = "building"
        self.belt_system.placing_belt = False

    def enter_delete_mode(self):
        self.build_mode = "deleting"
        self.belt_system.placing_belt = False

    def rotate_selected(self, steps=1):
        """Rotate whichever build target is selected (Splitter or belt
        facing) by `steps` quarter-turns clockwise. Negative steps rotate
        counter-clockwise (steps=-1 is one quarter-turn back); steps=2 is
        a 180-degree flip - same rotation either way, just applied
        multiple times."""
        if self.selected_machine_class is Splitter:
            self.machine_system.splitter_rotation_steps = (self.machine_system.splitter_rotation_steps + steps) % 4
        elif self.selected_machine_class is BeltSegment:
            direction = self.belt_system.belt_placement_direction
            for _ in range(steps % 4):
                direction = Vector2(-direction.y, direction.x)
            self.belt_system.belt_placement_direction = direction

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

    def reset_rotation(self):
        self.belt_system.belt_placement_direction = Vector2(1, 0)
        self.machine_system.splitter_rotation_steps = 0