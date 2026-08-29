# systems.machine_interaction_system
import pygame as py

from objects.machines.producing_machine import ProducingMachine
from objects.machines.storage import Storage
from objects.machines.splitter import Splitter

class MachineInteractionSystem:
    def __init__(self, world, build_system, machine_ui, camera, hand_crafting_ui, storage_ui, player_inventory_ui, belt_filter_ui, splitter_filter_ui, ui_manager):
        self.world = world
        self.build_system = build_system
        self.machine_ui = machine_ui
        self.camera = camera
        self.hand_crafting_ui = hand_crafting_ui
        self.storage_ui = storage_ui
        self.player_inventory_ui = player_inventory_ui
        self.belt_filter_ui = belt_filter_ui
        self.splitter_filter_ui = splitter_filter_ui
        self.ui_manager = ui_manager

        self.hovered_object = None  # machine or BeltSegment under the mouse - set by update_hover()

    def _object_at_screen_pos(self, mx, my):
        """The machine or BeltSegment occupying the world tile under
        screen position (mx, my), or None."""
        world_x = mx + self.camera.x
        world_y = my + self.camera.y
        grid_x, grid_y = self.world.snap_to_tile(world_x, world_y)

        machine = self.world.get_machine_at((grid_x, grid_y))
        if machine:
            return machine

        return self.world.belt_map.get((grid_x, grid_y))

    def _interaction_allowed(self):
        """Shared gating for anything that reaches into the world under the
        cursor (hover highlight, left-click to open a panel, C to pick a
        build type): only while nothing is already selected for
        building/deleting and no other UI panel has the click instead."""
        if self.build_system.build_mode is not None:
            return False
        return not (self.machine_ui.open or self.storage_ui.open
                    or self.belt_filter_ui.open or self.splitter_filter_ui.open)

    def update_hover(self):
        """Refreshes hovered_object once per frame - whatever machine or
        belt is under the mouse right now, but only while a click would
        actually do something with it. Used purely for the hover
        highlight; handle_click/handle_pick_key do their own independent
        lookup when they actually act."""
        self.hovered_object = None
        if not self._interaction_allowed():
            return

        self.hovered_object = self._object_at_screen_pos(*py.mouse.get_pos())

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return
        if just_placed_machine:
            return
        if not self._interaction_allowed():
            return

        obj = self._object_at_screen_pos(*event.pos)

        # Open the matching UI depending on what kind of object this is -
        # anything non-None that isn't one of the machine types must be a
        # belt, since _object_at_screen_pos only ever returns a machine or
        # a belt_map entry.
        if isinstance(obj, ProducingMachine):
            self.hand_crafting_ui.close()
            self.machine_ui.open_for(obj)
            self.player_inventory_ui.open = True
        elif isinstance(obj, Storage):
            self.hand_crafting_ui.close()
            self.storage_ui.open_for(obj)
            self.player_inventory_ui.open = True
        elif isinstance(obj, Splitter):
            self.hand_crafting_ui.close()
            self.splitter_filter_ui.open_for(obj)
        elif obj is not None:
            self.hand_crafting_ui.close()
            self.belt_filter_ui.open_for(obj)

    def handle_pick_key(self, event):
        """Pressing C while nothing is selected for building/deleting
        "picks" the type of whatever machine or belt the mouse is over into
        the build hotbar - the same effect as clicking its hotbar slot or
        pressing its number key - so you can immediately place more of
        what you're pointing at."""
        if event.type != py.KEYDOWN or event.key != py.K_c:
            return
        if not self._interaction_allowed():
            return

        obj = self._object_at_screen_pos(*py.mouse.get_pos())
        if obj is None:
            return

        self.ui_manager.close_all_uis()
        self.build_system.select_machine(type(obj))
        self.build_system.reset_rotation()