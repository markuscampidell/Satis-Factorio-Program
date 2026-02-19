# systems/build_system.py
import pygame as py

from objects.machines.splitter import Splitter
from objects.conveyors.conveyor_belt import BeltSegment

from core.vector2 import Vector2

class BuildSystem:
    def __init__(self, game):
        self.game = game

    def handle_placement(self, event):
        game = self.game
        if game.player_inventory_ui.open or game.machine_ui.open: return
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1: return

        mx, my = event.pos
        world_x = mx + game.camera.x
        world_y = my + game.camera.y

        # Delete mode
        if game.build_mode == "deleting":
            game.machine_placer.delete_machine(mx, my)
            game.belts.delete_belt(
                mx, my,
                delete_whole=bool(py.key.get_mods() & py.KMOD_SHIFT),
                camera_x=game.camera.x,
                camera_y=game.camera.y,
                player_inventory=game.player.inventory
            )
            self.update_all_splitters_outputs()
            return

        # Belt placement
        if game.build_mode == "building" and game.selected_machine_class is BeltSegment:
            if not game.placing_belt:
                if self._mouse_over_ui(mx, my):
                    return
                game.placing_belt = True
                game.belts.beltX1 = world_x
                game.belts.beltY1 = world_y
                return
            else:
                if self._mouse_over_ui(mx, my):
                    return
                game.belts.place_belt(world_x, world_y, game.selected_belt_type)
                self.update_all_splitters_outputs()
                game.placing_belt = False
                return

        # Machine placement
        if game.build_mode == "building" and game.selected_machine_class is not None:
            game.machine_placer.place_machine(game.selected_machine_class)
            if hasattr(game, 'preview_splitter'):
                game.preview_splitter = None

    def update_all_splitters_outputs(self):
        game = self.game
        cell = game.grid.CELL_SIZE
        for machine in game.world.machines:
            if isinstance(machine, Splitter):
                output_belts = []
                for direction in machine._get_relative_dirs():
                    next_rect = machine.rect.move(int(direction.x * cell), int(direction.y * cell))
                    seg = game.world.belt_map.get((next_rect.x, next_rect.y))
                    output_belts.append(seg)
                machine.output_belts = [b for b in output_belts if b]
                if machine.output_belts:
                    machine.current_output_index %= len(machine.output_belts)
                else:
                    machine.current_output_index = 0

    def update_hovered_delete_target(self):
        game = self.game
        if game.build_mode != "deleting":
            game.hovered_delete_target = None
            return

        mx, my = py.mouse.get_pos()
        world_x = mx + game.camera.x
        world_y = my + game.camera.y

        # Check machines first
        for machine in game.world.machines:
            if machine.rect.collidepoint(world_x, world_y):
                game.hovered_delete_target = machine
                return

        # Then check belts
        for seg in game.world.belt_segments:
            if seg.rect.collidepoint(world_x, world_y):
                game.hovered_delete_target = seg
                return

        game.hovered_delete_target = None

    # --- Helper ---
    def _mouse_over_ui(self, mx, my):
        game = self.game
        return ((game.machine_ui.open and game.machine_ui.rect.collidepoint(mx, my)) or
                (game.player_inventory_ui.open and game.player_inventory_ui.rect.collidepoint(mx, my)))