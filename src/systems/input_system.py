# systems.input_system
import pygame as py


class InputSystem:
    """Turns raw keyboard and mouse events into actual game actions -
    opening panels, entering delete mode, rotating what you're building,
    canceling things."""

    def __init__(self, build_system, ui_manager, hand_crafting_ui, machine_ui, player_inventory_ui, belt_system, machine_system, storage_ui, belt_filter_ui, splitter_filter_ui):
        self.build_system = build_system
        self.ui_manager = ui_manager
        self.hand_crafting_ui = hand_crafting_ui
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui
        self.belt_system = belt_system
        self.machine_system = machine_system
        self.storage_ui = storage_ui
        self.belt_filter_ui = belt_filter_ui
        self.splitter_filter_ui = splitter_filter_ui

    def handle_keys(self, event):
        """Reacts to a single key press - opening or closing panels,
        entering delete mode, rotating what's selected, and so on."""
        if event.type != py.KEYDOWN: return

        if event.key == py.K_ESCAPE:
            self.ui_manager.close_all_uis()
            self.build_system.reset_build_state()
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
                self.machine_ui.close()
                self.storage_ui.close()
                self.hand_crafting_ui.open = True
                self.player_inventory_ui.open = True
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
                    ui.crafting_mode = None
                else:
                    ui.crafting_mode = "auto"

                ui.progress = 0.0
            return


        if (self.player_inventory_ui.open or self.machine_ui.open or self.storage_ui.open
                or self.belt_filter_ui.open or self.splitter_filter_ui.open): return


        if event.key == py.K_r and self.build_system.build_mode == "building":
            if py.key.get_mods() & py.KMOD_SHIFT:
                self.build_system.rotate_selected(steps=-1)
            else:
                self.build_system.rotate_selected(steps=1)
            return

        if event.key == py.K_t and self.build_system.build_mode == "building":
            self.build_system.rotate_selected(steps=2)
            return

    def handle_mouse(self, event):
        """Reacts to a single mouse event - right click cancels whatever's
        in progress, left click gets passed on to whichever panel is open."""
        if event.type == py.MOUSEWHEEL:
            if self.hand_crafting_ui.open:
                self.hand_crafting_ui.handle_mouse(event)
            return

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
        """Backs out of whatever's in progress: cancels a belt drag that
        hasn't been finished yet, or just leaves build/delete mode."""
        if self.belt_system.placing_belt:
            self.belt_system.placing_belt = False
            return
        
        if self.build_system.build_mode == "building":
            self.build_system.reset_build_state()
            return
        
        if self.build_system.build_mode == "deleting":
            self.build_system.enter_build_mode()
            return