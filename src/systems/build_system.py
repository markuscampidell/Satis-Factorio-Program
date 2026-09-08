# systems.build_system
import pygame as py

from objects.machines.splitter import Splitter
from objects.conveyors.belt_segment import BeltSegment
from objects.machines.smelter import Smelter
from core.vector2 import Vector2

class BuildSystem:
    """Handles building and deleting: what mode you're in, what's
    selected, and actually placing or removing things when you click."""

    def __init__(self, world, player, camera, grid, belt_system, machine_system, machine_ui, player_inventory_ui, storage_ui, belt_filter_ui, splitter_filter_ui):
        self.world = world
        self.player = player
        self.camera = camera
        self.grid = grid
        self.belt_system = belt_system
        self.machine_system = machine_system
        self.machine_ui = machine_ui
        self.player_inventory_ui = player_inventory_ui
        self.storage_ui = storage_ui
        self.belt_filter_ui = belt_filter_ui
        self.splitter_filter_ui = splitter_filter_ui

        # Build state
        self.build_mode = None
        self.selected_machine_class = Smelter
        self.hovered_delete_target = None

        # Dedupe key for click-and-drag placing/deleting: the last tile
        # acted on while the mouse button's been held down, so a drag
        # places or deletes (at most) once per tile it crosses instead of
        # re-attempting on every single motion event.
        self._last_dragged_tile = None

        # The machine placed most recently during the current drag, if
        # any - passed to place_machine() as protected_machine so
        # dragging with Shift held to overwrite other things can't also
        # immediately overwrite the machine this same drag just placed.
        self._last_placed_machine = None

    def handle_placement(self, event):
        """Handles a click while in build or delete mode: places whatever's
        selected, starts/finishes dragging out a belt, or deletes what's
        under the cursor. Continuing to place/delete while the mouse
        button stays held is handled separately by update_drag(), called
        once per frame - not here, since events alone would miss it: the
        camera can pan underneath a perfectly still mouse (e.g. walking
        with WASD while holding the button down), changing what world tile
        is under the cursor without ever firing a MOUSEMOTION event."""
        if (self.player_inventory_ui.open or self.machine_ui.open or self.storage_ui.open
                or self.belt_filter_ui.open or self.splitter_filter_ui.open): return

        if event.type == py.MOUSEBUTTONUP and event.button == 1:
            self._last_dragged_tile = None
            self._last_placed_machine = None
            return

        if not (event.type == py.MOUSEBUTTONDOWN and event.button == 1):
            return

        mx, my = event.pos
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        if self.build_mode == "deleting":
            self._try_delete_at(mx, my, world_x, world_y)
            return

        # Belt placement - dragging out a belt line is its own separate
        # start-click/end-click gesture, not the held-down kind.
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

        if self.build_mode == "building" and self.selected_machine_class is not None:
            self._try_place_machine_at(mx, my, world_x, world_y)

    def update_drag(self):
        """Keeps placing or deleting, once per frame, for as long as the
        mouse button stays held - covers both dragging the mouse across
        new tiles and the camera panning a stationary mouse onto new
        tiles (see handle_placement's docstring), which a purely
        event-driven MOUSEMOTION check would miss entirely."""
        if (self.player_inventory_ui.open or self.machine_ui.open or self.storage_ui.open
                or self.belt_filter_ui.open or self.splitter_filter_ui.open): return
        if not py.mouse.get_pressed()[0]:
            return
        # Belt placement is its own click-to-click gesture, never a hold-drag.
        if self.build_mode == "building" and self.selected_machine_class is BeltSegment:
            return

        mx, my = py.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y

        if self.build_mode == "deleting":
            self._try_delete_at(mx, my, world_x, world_y)
        elif self.build_mode == "building" and self.selected_machine_class is not None:
            self._try_place_machine_at(mx, my, world_x, world_y)

    def _try_delete_at(self, mx, my, world_x, world_y):
        """Deletes whatever's at this screen position, unless it's the
        same tile the current drag already handled."""
        tile = self.world.snap_to_tile(world_x, world_y)
        if tile == self._last_dragged_tile:
            return

        deleted_machine = self.machine_system.delete_machine(mx, my)
        deleted_belt = self.belt_system.delete_belt(
            mx, my,
            delete_whole=bool(py.key.get_mods() & py.KMOD_SHIFT),
            camera_x=self.camera.x,
            camera_y=self.camera.y)

        # Only remember this tile as "done" if something actually got
        # deleted - a merely-blocked attempt (e.g. not enough inventory
        # room for the refund yet) stays eligible for a retry next frame
        # instead of being silently written off for the rest of this drag.
        if deleted_machine or deleted_belt:
            self._last_dragged_tile = tile
            self.belt_system.update_belt_incoming_directions()

    def _try_place_machine_at(self, mx, my, world_x, world_y):
        """Places the selected machine at this screen position, unless
        it's the same tile the current drag already handled."""
        tile = self.world.snap_to_tile(world_x, world_y)
        if tile == self._last_dragged_tile:
            return

        placed = self.machine_system.place_machine(
            self.selected_machine_class, protected_machine=self._last_placed_machine)

        # Only remember this tile as "done" if a machine actually went
        # down - a merely-blocked attempt (occupied without Shift held
        # yet, say) stays eligible for a retry next frame instead of being
        # silently written off for the rest of this drag, which is what
        # made holding Shift mid-drag look like it didn't do anything
        # until you let go and clicked again.
        if placed:
            self._last_dragged_tile = tile
            self._last_placed_machine = placed
            self.belt_system.update_belt_incoming_directions()
            if hasattr(self, 'preview_splitter'):
                self.preview_splitter = None

    def update_hovered_delete_target(self):
        """Figures out what's under the mouse right now, so delete mode
        can highlight it before you actually click it."""
        if self.build_mode != "deleting":
            self.hovered_delete_target = None
            return

        # Mouse grid coordinates
        mx, my = py.mouse.get_pos()
        grid_x = (mx + self.camera.x) // self.grid.CELL_SIZE
        grid_y = (my + self.camera.y) // self.grid.CELL_SIZE

        # Check machines by tile, then belts
        machine = self.world.machine_map.get((grid_x, grid_y))
        if machine:
            self.hovered_delete_target = machine
            return

        self.hovered_delete_target = self.world.belt_map.get((grid_x, grid_y))

    def _mouse_over_ui(self, mx, my):
        return ((self.machine_ui.open and self.machine_ui.rect.collidepoint(mx, my)) or
                (self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my)) or
                (self.storage_ui.open and self.storage_ui.rect.collidepoint(mx, my)) or
                (self.belt_filter_ui.open and self.belt_filter_ui.rect.collidepoint(mx, my)) or
                (self.splitter_filter_ui.open and self.splitter_filter_ui.rect.collidepoint(mx, my)))
    
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