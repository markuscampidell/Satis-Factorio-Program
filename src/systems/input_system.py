# systems/input_system.py
import pygame as py
from core.vector2 import Vector2

from objects.machines.assembler import Assembler
from objects.machines.smelter import Smelter
from objects.machines.splitter import Splitter
from objects.conveyors.belt_segment import BeltSegment

from ui.ui_manager import UIManager


class InputSystem:
    def __init__(self, game):
        self.game = game
        self.ui_manager = UIManager(game)

    def handle_keys(self, event):
        game = self.game
        if event.type != py.KEYDOWN:
            return

        if event.key == py.K_ESCAPE:
            self.ui_manager.close_all_uis()
            game.build_mode = None
            self.reset_build_state()
            game.selected_machine_class = None
            return

        if event.key == py.K_q:
            self.ui_manager.close_all_uis()
            if game.build_mode == "building":
                game.build_mode = None
                self.reset_build_state()
            else:
                game.build_mode = "building"
                game.placing_belt = False
            return

        if event.key == py.K_x:
            self.ui_manager.close_all_uis()

            game.placing_belt = False
            if game.build_mode == "deleting":
                game.build_mode = None
            else: 
                game.build_mode = "deleting"
                
            return

        if event.key == py.K_i:
            if game.machine_ui.open and game.machine_ui.selected_machine:
                machine = game.machine_ui.selected_machine
                for item_id, amount in machine.recipe.inputs.items():
                    if item_id in machine.input_inventories:
                        inv = machine.input_inventories[item_id]
                        inv.try_add_items(item_id, amount)
            return

        if event.key == py.K_f:
            # Opening crafting UI cancels build
            if not game.crafting_ui.open:
                self.reset_build_state()
                game.build_mode = None
                game.crafting_ui.open = True
            else:
                game.crafting_ui.close()
            return

        if event.key == py.K_TAB:
            # Opening inventory cancels build
            if not game.player_inventory_ui.open:
                self.reset_build_state()
                game.build_mode = None
            self.ui_manager.toggle_ui("player_inventory")
            return

        if game.crafting_ui.open:
            if event.key == py.K_SPACE:
                game.crafting_ui.auto_crafting = not game.crafting_ui.auto_crafting
                game.crafting_ui.progress = 0.0
            return
        
        if game.player_inventory_ui.open or game.machine_ui.open:
            return

        if event.key == py.K_r and game.build_mode == "building":
            if game.selected_machine_class is Splitter:
                game.splitter_rotation_steps = (game.splitter_rotation_steps + 1) % 4
            elif game.selected_machine_class is BeltSegment:
                x, y = game.belts.belt_placement_direction.x, game.belts.belt_placement_direction.y
                game.belts.belt_placement_direction = Vector2(-y, x)

        if event.key == py.K_t:
            if game.build_mode == "building" and \
               game.selected_machine_class is BeltSegment and \
               game.placing_belt:
                game.belts.belt_first_axis_horizontal = not game.belts.belt_first_axis_horizontal

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

        if event.type != py.MOUSEBUTTONDOWN:
            return

        # Right click cancels build/delete
        if event.button == 3:
            self.cancel_build_or_delete()
            self.reset_rotation()
            return

        # Left click for world interactions
        if event.button == 1:
            # 1️⃣ Check UIs first (they get priority)
            if game.crafting_ui.open:
                game.crafting_ui.handle_mouse(event)
                return
            
            if game.machine_ui.open:
                game.machine_ui.handle_event(event, game.just_placed_machine, game.build_mode == "building")
                return
            
            

    def cancel_build_or_delete(self):
        game = self.game
        
        if game.placing_belt:
            game.placing_belt = False
            return
        
        if game.build_mode == "building":
            game.build_mode = None
            self.reset_rotation()
            return
        
        if game.build_mode == "deleting":
            game.build_mode = "building"
            return

    def reset_build_state(self):
        game = self.game
        game.selected_machine_class = Smelter
        game.placing_belt = False
        self.reset_rotation()
        game.belts.belt_first_axis_horizontal = True
    
    def reset_rotation(self):
        game = self.game
        game.belts.belt_placement_direction = Vector2(1, 0)
        game.belts.splitter_rotation_steps = 0
