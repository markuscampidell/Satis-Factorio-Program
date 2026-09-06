# systems.machine_interaction_system
import pygame as py

from objects.machines.producing_machine import ProducingMachine
from objects.machines.storage import Storage
from objects.machines.splitter import Splitter

class MachineInteractionSystem:
    """Handles clicking on a machine or belt out in the world - opens
    whichever panel matches what you clicked, and keeps track of what's
    currently hovered for the highlight effect."""

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

    def _interaction_allowed(self, mx, my):
        """Shared gating for anything that reaches into the world under the
        cursor (hover highlight, left-click to open a panel, C to pick a
        build type): not while placing/deleting, and not while the cursor
        is actually over one of the UI panels currently on screen.

        Deliberately NOT "blocked whenever any panel is open" - clicking a
        *different* world object while a panel is already open is
        supposed to work (each panel closes itself when a click lands
        outside it, then this same click opens the new one), so the only
        thing that actually needs blocking is the panels' own screen
        space, not the mere fact that some panel happens to be open
        elsewhere on screen."""
        if self.build_system.build_mode is not None:
            return False

        open_uis = (self.machine_ui, self.storage_ui, self.belt_filter_ui,
                    self.splitter_filter_ui, self.player_inventory_ui, self.hand_crafting_ui)
        return not any(ui.open and ui.rect.collidepoint(mx, my) for ui in open_uis)

    def update_hover(self):
        """Refreshes hovered_object once per frame - whatever machine or
        belt is under the mouse right now, but only while a click would
        actually do something with it. Used purely for the hover
        highlight; handle_click/handle_pick_key do their own independent
        lookup when they actually act."""
        mx, my = py.mouse.get_pos()
        self.hovered_object = None
        if not self._interaction_allowed(mx, my):
            return

        self.hovered_object = self._object_at_screen_pos(mx, my)

    def handle_click(self, event, just_placed_machine):
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return
        if just_placed_machine:
            return
        mx, my = event.pos
        if not self._interaction_allowed(mx, my):
            return

        obj = self._object_at_screen_pos(mx, my)

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
            self.player_inventory_ui.open = False
            self.splitter_filter_ui.open_for(obj)
        elif obj is not None:
            self.hand_crafting_ui.close()
            self.player_inventory_ui.open = False
            self.belt_filter_ui.open_for(obj)

    def handle_pick_key(self, event):
        """Pressing C while nothing is selected for building/deleting
        "picks" the type of whatever machine or belt the mouse is over into
        the build hotbar - the same effect as clicking its hotbar slot or
        pressing its number key - so you can immediately place more of
        what you're pointing at."""
        if event.type != py.KEYDOWN or event.key != py.K_c:
            return
        mx, my = py.mouse.get_pos()
        if not self._interaction_allowed(mx, my):
            return

        obj = self._object_at_screen_pos(mx, my)
        if obj is None:
            return

        self.ui_manager.close_all_uis()
        self.build_system.select_machine(type(obj))
        self.build_system.reset_rotation()