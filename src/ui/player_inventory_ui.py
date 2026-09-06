# ui.player_inventory_ui
import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory_transfer import move_stack, move_all_of_type
from ui.modifier_keys import get_shift_ctrl
from ui.slot_drawing import draw_item_slot_contents, draw_hovered_item_tooltip

class PlayerInventoryUI:
    """Draws the player's own inventory grid, and lets you shift/ctrl-click
    items into whatever other panel happens to be open."""

    SLOT_SIZE = 48
    PADDING = 10
    TITLE_HEIGHT = 40

    def __init__(self, player, get_screen_size, panel_side="left"):
        self.player = player
        self.get_screen_size = get_screen_size
        self.panel_side = panel_side
        self.open = False

        self.width = self.player.inventory.width * self.SLOT_SIZE + self.PADDING * 2
        self.height = self.player.inventory.height * self.SLOT_SIZE + self.PADDING * 2 + self.TITLE_HEIGHT

        # Panel Surface
        self.sprite = py.Surface((self.width, self.height), py.SRCALPHA)
        py.draw.rect(self.sprite, (202, 200, 228, 220), self.sprite.get_rect(), border_radius=18)

        # Initial position; we'll update Y each draw
        screen_w, screen_h = self.get_screen_size()
        x = 0 if self.panel_side == "left" else screen_w - self.width
        self.rect = self.sprite.get_rect(x=x, centery=screen_h // 2)

        self.font_small = py.font.SysFont("Arial", 14)
        self.font_tooltip = py.font.SysFont("Arial", 16)
        self.font_title = py.font.SysFont("Arial", 22)

        # Hover
        self.slot_rects = []

    def draw(self, screen):
        if not self.open:
            return

        # Always recalc screen size and update position
        screen_w, screen_h = self.get_screen_size()
        self.rect.centery = screen_h // 2
        self.rect.x = 0 if self.panel_side == "left" else screen_w - self.width

        screen.blit(self.sprite, self.rect.topleft)

        title = self.font_title.render("Inventory", True, "#000000")
        screen.blit(title, title.get_rect(midtop=(self.rect.centerx, self.rect.y + 8)))

        self._draw_grid_slots(screen)
        self._handle_hover(screen)

    def _draw_grid_slots(self, screen):
        self.slot_rects = []

        for y in range(self.player.inventory.height):
            for x in range(self.player.inventory.width):
                left = self.rect.x + self.PADDING + x * self.SLOT_SIZE
                top = self.rect.y + self.PADDING + self.TITLE_HEIGHT + y * self.SLOT_SIZE
                width = self.SLOT_SIZE
                height = self.SLOT_SIZE

                slot_rect = py.Rect(left, top, width, height)

                py.draw.rect(screen, "#AAAAAA", slot_rect, 2)

                slot = self.player.inventory.slots[y][x]

                if slot:
                    draw_item_slot_contents(screen, slot, slot_rect, self.font_small)

                    # Save for hover detection / click handling
                    item = get_item_by_id(slot["item"])
                    self.slot_rects.append((slot_rect, item, x, y))

    def _handle_hover(self, screen):
        hover_entries = [(rect, item) for rect, item, x, y in self.slot_rects]
        draw_hovered_item_tooltip(screen, self.font_tooltip, hover_entries)

    def handle_event(self, event, machine_ui, storage_ui):
        """Shift+click a slot to move that stack into whichever other panel
        is currently open (a Storage's flat inventory, or a producing
        machine's matching input/output inventory); Ctrl+click moves every
        stack of that item type instead. Plain left click does nothing.
        No-op if neither panel is open, or the item doesn't belong there."""
        if not self.open:
            return
        if event.type != py.MOUSEBUTTONDOWN or event.button != 1:
            return

        shift_held, ctrl_held = get_shift_ctrl()
        if not (shift_held or ctrl_held):
            return

        mx, my = event.pos
        for rect, item, x, y in self.slot_rects:
            if rect.collidepoint(mx, my):
                self._transfer_slot(x, y, item.item_id, shift_held, machine_ui, storage_ui)
                return

    def _transfer_slot(self, x, y, expected_item_id, shift_held, machine_ui, storage_ui):
        """Moves this slot's stack (or every stack of that item type) into
        whichever other panel is open, double-checking the item hasn't
        changed since this slot was last drawn."""
        source = self.player.inventory

        if storage_ui.open and storage_ui.selected_storage:
            dest = storage_ui.selected_storage.inventory
        elif machine_ui.open and machine_ui.selected_machine:
            slot = source.slots[y][x]
            if not slot or slot["item"] != expected_item_id:
                return  # the grid changed since this was drawn - safer to no-op than act on the wrong item
            machine = machine_ui.selected_machine
            input_inventories = getattr(machine, "input_inventories", {})
            output_inventories = getattr(machine, "output_inventories", {})
            dest = input_inventories.get(slot["item"]) or output_inventories.get(slot["item"])
            if dest is None:
                return  # item type not accepted by this machine
        else:
            return

        if shift_held:
            move_stack(source, x, y, dest, expected_item_id)
        else:
            move_all_of_type(source, x, y, dest, expected_item_id)

    def close(self):
        self.open = False