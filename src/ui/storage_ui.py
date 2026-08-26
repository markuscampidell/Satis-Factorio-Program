# ui.storage_ui
import pygame as py

from objects.machines.storage import Storage
from entities.inventory_transfer import move_stack, move_all_of_type


class StorageUI:
    """State and interaction (open/close, shift/ctrl-click to take) for a
    Storage building's panel - always centered on screen while open,
    following the same open/close/auto-close pattern as ProducingMachineUI.
    Plain left click does nothing to items; Shift+click moves one stack to
    the player, Ctrl+click moves every stack of that item type. Moving
    items the other way (player -> storage) is handled by
    PlayerInventoryUI, since that's where the click originates. Drawing
    lives in StorageUIRenderer."""

    SLOT_SIZE = 48
    PADDING = 10
    TITLE_HEIGHT = 40

    def __init__(self, camera, player, player_inventory_ui, panel_side="right"):
        self.width = Storage.INVENTORY_WIDTH * self.SLOT_SIZE + self.PADDING * 2
        self.height = Storage.INVENTORY_HEIGHT * self.SLOT_SIZE + self.TITLE_HEIGHT + self.PADDING

        self.sprite = py.Surface((self.width, self.height), py.SRCALPHA)
        py.draw.rect(self.sprite, "#CAC8E4", self.sprite.get_rect(), border_radius=18)
        self.sprite.set_alpha(220)
        self.rect = self.sprite.get_rect(center=(camera.screen_width // 2, camera.screen_height // 2))

        self.open = False
        self.selected_storage = None

        self.camera = camera
        self.player = player
        self.player_inventory_ui = player_inventory_ui
        self.panel_side = panel_side

        self.slot_rects = []  # [(rect, x, y)] - populated by the renderer each frame

    def handle_event(self, event, just_placed, placing_machine):
        if placing_machine or just_placed:
            return
        if event.type == py.VIDEORESIZE:
            return

        mx, my = getattr(event, "pos", (None, None))
        left_click = event.type == py.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1

        if self.open and self.selected_storage:
            if left_click and mx is not None:
                self._handle_slot_click(mx, my)
            self._handle_close_click(left_click, mx, my)
            self._handle_visibility()

    def _handle_slot_click(self, mx, my):
        """Plain left click does nothing. Shift+click moves that slot's
        stack to the player's inventory; Ctrl+click moves every stack of
        that same item type."""
        mods = py.key.get_mods()
        shift_held = bool(mods & py.KMOD_SHIFT)
        ctrl_held = bool(mods & py.KMOD_CTRL)
        if not (shift_held or ctrl_held):
            return

        for rect, x, y in self.slot_rects:
            if rect.collidepoint(mx, my):
                inv = self.selected_storage.inventory
                if shift_held:
                    move_stack(inv, x, y, self.player.inventory)
                else:
                    move_all_of_type(inv, x, y, self.player.inventory)
                return

    def _handle_close_click(self, left_click, mx, my):
        if not left_click:
            return
        if mx is not None and my is not None:
            if self.rect.collidepoint(mx, my):
                return
            if self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my):
                return
        self.close()

    def _handle_visibility(self):
        if not self.selected_storage:
            return
        viewport = py.Rect(0, 0, self.camera.screen_width, self.camera.screen_height)
        if not viewport.colliderect(self.selected_storage.rect.move(-self.camera.x, -self.camera.y)):
            self.close()

    def close(self):
        self.open = False
        self.selected_storage = None

    def open_for(self, storage):
        self.open = True
        self.selected_storage = storage
