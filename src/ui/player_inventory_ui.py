# ui.player_inventory_ui
import pygame as py

from constants.itemdata import get_item_by_id
from entities.inventory_transfer import move_stack, move_all_of_type
from ui.modifier_keys import get_shift_ctrl
from ui.slot_drawing import draw_item_slot_contents

class PlayerInventoryUI:
    SLOT_SIZE = 48
    PADDING = 10

    def __init__(self, player, get_screen_size, panel_side="left"):
        self.player = player
        self.get_screen_size = get_screen_size
        self.panel_side = panel_side
        self.open = False

        self.width = self.player.inventory.width * self.SLOT_SIZE + self.PADDING * 2
        self.height = self.player.inventory.height * self.SLOT_SIZE + self.PADDING * 2

        # Panel Surface
        self.sprite = py.Surface((self.width, self.height), py.SRCALPHA)
        py.draw.rect(self.sprite, (202, 200, 228, 220), self.sprite.get_rect(), border_radius=18)

        # Initial position; we'll update Y each draw
        screen_w, screen_h = self.get_screen_size()
        x = 0 if self.panel_side == "left" else screen_w - self.width
        self.rect = self.sprite.get_rect(x=x, centery=screen_h // 2)

        self.font_small = py.font.SysFont("Arial", 14)
        self.font_tooltip = py.font.SysFont("Arial", 16)

        # Hover
        self.slot_rects = []
        self._hovered_item = None
        self._tooltip_visible = False

    def draw(self, screen):
        if not self.open:
            return

        # Always recalc screen size and update position
        screen_w, screen_h = self.get_screen_size()
        self.rect.centery = screen_h // 2
        self.rect.x = 0 if self.panel_side == "left" else screen_w - self.width

        screen.blit(self.sprite, self.rect.topleft)

        self._draw_grid_slots(screen)
        self._handle_hover(screen)

    def _draw_grid_slots(self, screen):
        self.slot_rects = []

        for y in range(self.player.inventory.height):
            for x in range(self.player.inventory.width):
                left = self.rect.x + self.PADDING + x * self.SLOT_SIZE
                top = self.rect.y + self.PADDING + y * self.SLOT_SIZE
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
        mx, my = py.mouse.get_pos()
        hovered_item = None

        for rect, item, x, y in self.slot_rects:
            if rect.collidepoint(mx, my):
                hovered_item = item
                break

        if hovered_item != self._hovered_item:
            self._hovered_item = hovered_item
            self._tooltip_visible = False

        elif hovered_item: self._tooltip_visible = True

        else: self._tooltip_visible = False

        if self._tooltip_visible and self._hovered_item:
            self._draw_tooltip(screen, self._hovered_item.name, (mx, my))

    def _draw_tooltip(self, screen, text, pos):
        padding = 8

        text_surf = self.font_tooltip.render(text, True, "#000000")

        width = text_surf.get_width() + padding * 2
        height = text_surf.get_height() + padding * 2

        x = pos[0] + 15
        y = pos[1] + 15

        # Bildschirmgrenzen prüfen
        if x + width > screen.get_width():
            x = screen.get_width() - width - 5
        if y + height > screen.get_height():
            y = screen.get_height() - height - 5

        panel_color = (202, 200, 228, 220)

        tooltip_surface = py.Surface((width, height), py.SRCALPHA)
        py.draw.rect(tooltip_surface, panel_color, tooltip_surface.get_rect(), border_radius=12)

        tooltip_surface.blit(text_surf, (padding, padding))
        screen.blit(tooltip_surface, (x, y))

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
                self._transfer_slot(x, y, shift_held, machine_ui, storage_ui)
                return

    def _transfer_slot(self, x, y, shift_held, machine_ui, storage_ui):
        source = self.player.inventory

        if storage_ui.open and storage_ui.selected_storage:
            dest = storage_ui.selected_storage.inventory
        elif machine_ui.open and machine_ui.selected_machine:
            slot = source.slots[y][x]
            if not slot:
                return
            machine = machine_ui.selected_machine
            input_inventories = getattr(machine, "input_inventories", {})
            output_inventories = getattr(machine, "output_inventories", {})
            dest = input_inventories.get(slot["item"]) or output_inventories.get(slot["item"])
            if dest is None:
                return  # item type not accepted by this machine
        else:
            return

        if shift_held:
            move_stack(source, x, y, dest)
        else:
            move_all_of_type(source, x, y, dest)

    def close(self):
        self.open = False