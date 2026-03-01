# systems.input_system
import pygame as py

from objects.machines.assembler import Assembler
from objects.machines.smelter import Smelter
from objects.machines.splitter import Splitter
from objects.conveyors.belt_segment import BeltSegment


class InputSystem:
    def __init__(self, build_system, ui_manager, hand_crafting_ui, machine_ui, player_inventory_ui, belt_system, machine_system):
        self.build_system = build_system
        self.ui_manager = ui_manager
        self.hand_crafting_ui = hand_crafting_ui
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui
        self.belt_system = belt_system
        self.machine_system = machine_system

    def handle_keys(self, event):
        if event.type != py.KEYDOWN: return

        if event.key == py.K_ESCAPE:
            self.ui_manager.close_all_uis()
            self.build_system.reset_build_state()
            return

        if event.key == py.K_q:
            self.ui_manager.close_all_uis()
            if self.build_system.build_mode == "building": self.build_system.reset_build_state()
            else: self.build_system.enter_build_mode()
            return

        if event.key == py.K_x:
            self.ui_manager.close_all_uis()
            self.build_system.toggle_delete_mode()
            return

        if event.key == py.K_i:
            if self.machine_ui.open and self.machine_ui.selected_machine:
                machine = self.machine_ui.selected_machine
                for item_id, amount in machine.recipe.inputs.items():
                    if item_id in machine.input_inventories:
                        inv = machine.input_inventories[item_id]
                        inv.try_add_items(item_id, amount)
            return

        if event.key == py.K_f:
            if not self.hand_crafting_ui.open:
                self.build_system.reset_build_state()
                self.hand_crafting_ui.open = True
            else:
                self.hand_crafting_ui.close()
            return

        if event.key == py.K_TAB:
            if not self.player_inventory_ui.open:
                self.build_system.reset_build_state()
            self.ui_manager.toggle_ui("player_inventory")
            return

        if self.hand_crafting_ui.open:
            if event.key == py.K_SPACE:
                ui = self.hand_crafting_ui

                if ui.crafting_mode == "auto":
                    ui.crafting_mode = "none"
                else:
                    ui.crafting_mode = "auto"

                ui.progress = 0.0
            return


        if self.player_inventory_ui.open or self.machine_ui.open: return


        if event.key == py.K_r and self.build_system.build_mode == "building":
            self.build_system.rotate_selected()
            return

        if (event.key == py.K_t
            and self.build_system.build_mode == "building"
            and self.build_system.selected_machine_class is BeltSegment
            and self.belt_system.placing_belt):
            self.belt_system.belt_first_axis_horizontal = not self.belt_system.belt_first_axis_horizontal
            return

        if self.build_system.build_mode in ("building", "deleting"):
            machine_map = {py.K_1: Smelter,
                           py.K_2: Assembler,
                           py.K_3: BeltSegment,
                           py.K_4: Splitter,}

            if event.key in machine_map:
                self.build_system.select_machine(machine_map[event.key])

                if self.build_system.build_mode == "deleting":
                    self.build_system.enter_build_mode()

                return

    def handle_mouse(self, event):
        if event.type != py.MOUSEBUTTONDOWN: return

        # Right click
        if event.button == 3:
            self.cancel_build_or_delete()
            return

        # Left click
        if event.button == 1:
            if self.hand_crafting_ui.open:
                self.hand_crafting_ui.handle_mouse(event)
                return

            if self.machine_ui.open:
                self.machine_ui.handle_event(event, self.machine_system.just_placed_machine, self.build_system.build_mode == "building")
                return

    def cancel_build_or_delete(self):
        if self.belt_system.placing_belt:
            self.belt_system.placing_belt = False
            self.belt_system.belt_first_axis_horizontal = True
            return
        
        if self.build_system.build_mode == "building":
            self.build_system.reset_build_state()
            return
        
        if self.build_system.build_mode == "deleting":
            self.build_system.enter_build_mode()
            return