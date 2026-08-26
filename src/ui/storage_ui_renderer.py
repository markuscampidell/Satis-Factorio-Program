# ui.storage_ui_renderer
import pygame as py

from constants.itemdata import get_item_by_id


class StorageUIRenderer:
    """Draws a StorageUI's panel: background, title, and a flat grid of
    item slots - click one (handled in StorageUI) to withdraw it to the
    player's inventory. Not to be confused with drawing the Storage
    building's in-world sprite on the map - that's Storage.draw(), called
    from WorldRenderer. This only draws the popup panel."""

    def __init__(self, storage_ui):
        self.ui = storage_ui
        self.title_font = py.font.SysFont("Arial", 22)
        self.font_small = py.font.SysFont("Arial", 14)

    def draw(self, screen):
        ui = self.ui
        if not ui.open or not ui.selected_storage:
            return

        # Always centered - no dragging, so this can't drift off-screen.
        ui.rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        screen.blit(ui.sprite, ui.rect)

        title = self.title_font.render("Storage", True, "#000000")
        screen.blit(title, title.get_rect(midtop=(ui.rect.centerx, ui.rect.y + 8)))

        self._draw_slots(screen, ui)

    def _draw_slots(self, screen, ui):
        inv = ui.selected_storage.inventory
        ui.slot_rects = []

        grid_top = ui.rect.y + ui.TITLE_HEIGHT

        for y in range(inv.height):
            for x in range(inv.width):
                left = ui.rect.x + ui.PADDING + x * ui.SLOT_SIZE
                top = grid_top + y * ui.SLOT_SIZE
                slot_rect = py.Rect(left, top, ui.SLOT_SIZE, ui.SLOT_SIZE)
                py.draw.rect(screen, "#AAAAAA", slot_rect, 2)

                slot = inv.slots[y][x]
                if slot:
                    item = get_item_by_id(slot["item"])
                    if item and item.sprite:
                        size = ui.SLOT_SIZE - 10
                        img = item.get_scaled_sprite(size) if hasattr(item, "get_scaled_sprite") else py.transform.scale(item.sprite, (size, size))
                        if img:
                            screen.blit(img, (slot_rect.x + 5, slot_rect.y + 5))

                    text = self.font_small.render(str(slot["amount"]), True, "#000000")
                    screen.blit(text, text.get_rect(bottomright=(slot_rect.right - 5, slot_rect.bottom - 5)))

                ui.slot_rects.append((slot_rect, x, y))
