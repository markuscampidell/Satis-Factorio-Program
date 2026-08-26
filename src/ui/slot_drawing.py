# ui.slot_drawing
import pygame as py

from constants.itemdata import get_item_by_id


def draw_item_slot_contents(screen, slot, rect, amount_font, margin=5):
    """Draws an inventory slot's contents (item icon + stack-size text)
    inside `rect` - shared by every panel that renders a grid of item slots
    (player inventory, storage, machine input/output). Does not draw the
    slot's border - callers already draw that themselves, since some draw
    it even for empty slots."""
    if not slot:
        return

    item = slot["item"]
    item = get_item_by_id(item) if isinstance(item, str) else item

    if item and getattr(item, "sprite", None):
        size = rect.width - margin * 2
        img = item.get_scaled_sprite(size) if hasattr(item, "get_scaled_sprite") else py.transform.scale(item.sprite, (size, size))
        if img:
            screen.blit(img, (rect.x + margin, rect.y + margin))

    text = amount_font.render(str(slot["amount"]), True, "#000000")
    screen.blit(text, text.get_rect(bottomright=(rect.right - margin, rect.bottom - margin)))
