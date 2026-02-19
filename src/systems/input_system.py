# systems/input_system.py
import pygame as py
from core.vector2 import Vector2

from objects.machines.assembler import Assembler
from objects.machines.smelter import Smelter
from objects.machines.splitter import Splitter
from objects.conveyors.conveyor_belt import BeltSegment

class InputSystem:
    def __init__(self, game):
        self.game = game
        
    def handle_keys(self, event):
        game = self.game
        if event.type != py.KEYDOWN:
            return

        # ESCAPE: Close UIs & cancel build
        if event.key == py.K_ESCAPE:
            game.player_inventory_ui.close()
            game.machine_ui.close()
            game.build_mode = None
            self.reset_build_state()
            game.splitter_rotation_steps = 0
            game.belts.belt_placement_direction = Vector2(1, 0)
            game.selected_machine_class = None
            game.paused_mode = None
            return

        # TAB: Toggle inventory
        if event.key == py.K_TAB:
            if not game.player_inventory_ui.open:
                if game.build_mode is not None:
                    game.paused_mode = game.build_mode
                    game.build_mode = None
                game.player_inventory_ui.open = True
            else:
                if game.paused_mode is not None:
                    game.build_mode = game.paused_mode
                    game.machine_ui.close()
                    game.paused_mode = None
                game.player_inventory_ui.close()
            return

        # Q: Toggle build mode
        if event.key == py.K_q:
            game.player_inventory_ui.close()
            game.machine_ui.close()
            if game.build_mode == "building":
                game.build_mode = None
                self.reset_build_state()
                game.splitter_rotation_steps = 0
                game.belts.belt_placement_direction = Vector2(1, 0)
            else:
                game.build_mode = "building"
                game.placing_belt = False
            return

        # X: Toggle delete mode
        if event.key == py.K_x:
            if game.player_inventory_ui.open:
                game.player_inventory_ui.close()
                game.paused_mode = None
            if game.machine_ui.open:
                game.machine_ui.close()
            if game.build_mode == "deleting":
                game.build_mode = 'building'
            else:
                game.build_mode = "deleting"
                game.placing_belt = False
            return

        # I: Fill selected machine inputs
        if event.key == py.K_i:
            if game.machine_ui.open and game.machine_ui.selected_machine:
                machine = game.machine_ui.selected_machine
                for item_id, amount in machine.recipe.inputs.items():
                    if item_id in machine.input_inventories:
                        inv = machine.input_inventories[item_id]
                        inv.try_add_items(item_id, amount)
            return

        # Ignore other keys if UI is open
        if game.player_inventory_ui.open or game.machine_ui.open:
            return

        # R: Rotate machine / belt
        if event.key == py.K_r:
            if game.build_mode != "building":
                return
            if game.selected_machine_class is Splitter:
                game.splitter_rotation_steps = (game.splitter_rotation_steps + 1) % 4
            elif game.selected_machine_class is BeltSegment:
                x, y = game.belts.belt_placement_direction.x, game.belts.belt_placement_direction.y
                game.belts.belt_placement_direction = Vector2(-y, x)

        # T: Toggle belt axis
        if event.key == py.K_t:
            if (game.build_mode != "building" or
                game.selected_machine_class is not BeltSegment or
                not game.placing_belt):
                return
            game.belts.belt_first_axis_horizontal = not game.belts.belt_first_axis_horizontal

        # Number keys: Select machine type
        if game.build_mode in ("building", "deleting"):
            if event.key in (py.K_1, py.K_2, py.K_3, py.K_4):
                if event.key == py.K_1:
                    game.selected_machine_class = Smelter
                elif event.key == py.K_2:
                    game.selected_machine_class = Assembler
                elif event.key == py.K_3:
                    game.selected_machine_class = BeltSegment
                    game.selected_belt_type = "basic"
                elif event.key == py.K_4:
                    game.selected_machine_class = Splitter

                game.splitter_rotation_steps = 0
                game.belts.belt_placement_direction = Vector2(1, 0)

                if game.selected_machine_class is not BeltSegment:
                    game.placing_belt = False

                if game.build_mode == "deleting":
                    game.build_mode = "building"

    def handle_mouse(self, event):
        game = self.game
        if game.machine_ui.open or game.player_inventory_ui.open:
            return
        if event.type != py.MOUSEBUTTONDOWN or event.button != 3:
            return

        if game.build_mode == "deleting":
            game.build_mode = "building"
        elif game.placing_belt:
            game.placing_belt = False
        else:
            game.build_mode = None
            self.reset_build_state()
    
    # --- Build State Reset ---
    def reset_build_state(self):
        game = self.game
        game.placing_belt = False
        game.belts.belt_placement_direction = Vector2(1, 0)
        game.belts.splitter_rotation_steps = 0
        game.belts.belt_first_axis_horizontal = True