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


def draw_item_name_tooltip(screen, font, text, pos):
    """A small rounded label showing `text`, positioned just past `pos`
    (typically the mouse) and nudged back on screen if it would otherwise
    spill past an edge. Shared by every panel that shows item icons, so
    hovering one looks and behaves the same everywhere."""
    padding = 8

    text_surf = font.render(text, True, "#000000")

    width = text_surf.get_width() + padding * 2
    height = text_surf.get_height() + padding * 2

    x = pos[0] + 15
    y = pos[1] + 15

    if x + width > screen.get_width():
        x = screen.get_width() - width - 5
    if y + height > screen.get_height():
        y = screen.get_height() - height - 5

    panel_color = (202, 200, 228, 220)

    tooltip_surface = py.Surface((width, height), py.SRCALPHA)
    py.draw.rect(tooltip_surface, panel_color, tooltip_surface.get_rect(), border_radius=12)

    tooltip_surface.blit(text_surf, (padding, padding))
    screen.blit(tooltip_surface, (x, y))


def draw_hovered_item_tooltip(screen, font, hover_entries, mouse_pos=None):
    """Finds whichever (rect, item) pair in `hover_entries` the mouse is
    currently over and draws a name tooltip for it - `item` may be an Item
    instance, an item_id string, or None/empty (skipped, nothing drawn for
    that entry). Draws at most one tooltip, for the first match. This is
    the shared hover behavior for every panel that shows a grid of item
    icons - player inventory, storage, machine input/output slots, recipe
    lists, item filter pickers."""
    mx, my = mouse_pos if mouse_pos is not None else py.mouse.get_pos()

    for rect, item in hover_entries:
        if not item or not rect.collidepoint(mx, my):
            continue

        item = get_item_by_id(item) if isinstance(item, str) else item
        if item:
            draw_item_name_tooltip(screen, font, item.name, (mx, my))
        return
