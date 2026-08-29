# ui.item_filter_panel
import pygame as py

from constants.itemdata import ITEMS, get_item_by_id
from objects.item_filter import ItemFilter

SLOT_SIZE = 36
SLOT_GAP = 4


def _grid_cell_rect(top_left, index, columns):
    x, y = top_left
    col = index % columns
    row = index // columns
    slot_x = x + col * (SLOT_SIZE + SLOT_GAP)
    slot_y = y + row * (SLOT_SIZE + SLOT_GAP)
    return py.Rect(slot_x, slot_y, SLOT_SIZE, SLOT_SIZE)


def _grid_size(count, columns):
    rows = -(-count // columns)  # ceil division
    width = columns * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP
    height = rows * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP
    return width, height


class ItemFilterPanel:
    """Reusable checkbox + fixed grid of ItemFilter.SLOT_COUNT slots bound
    to one ItemFilter at a time. Ticking the filter reveals the (initially
    empty) slots; left-clicking an unfilled or filled slot calls
    `on_slot_click(item_filter, slot_index)` - the owning UI (BeltFilterUI/
    SplitterFilterUI) reacts by opening its shared ItemPickerOverlay, drawn
    in its own reserved area rather than in place of these slots; right-
    clicking a filled slot empties it directly, no picker involved. Not an
    open/close UI on its own - BeltFilterUI/SplitterFilterUI own the
    open/close/visibility lifecycle and just draw/click through one (or
    several, for a splitter's three sides) of these per frame."""

    CHECKBOX_SIZE = 20

    def __init__(self, columns=5, on_slot_click=None):
        self.columns = columns
        self.on_slot_click = on_slot_click
        self.checkbox_rect = None
        self.slot_rects = []  # [(rect, slot_index)]

        self.label_font = py.font.SysFont("Arial", 18, bold=True)
        self.checkbox_font = py.font.SysFont("Arial", 15)

    def content_size(self, with_label=True):
        grid_width, grid_height = _grid_size(ItemFilter.SLOT_COUNT, self.columns)

        label_height = self.label_font.get_height() + 6 if with_label else 0
        height = label_height + self.CHECKBOX_SIZE + 8 + grid_height

        checkbox_label_width = self.checkbox_font.size("Filter enabled")[0]
        min_width = self.CHECKBOX_SIZE + 8 + checkbox_label_width
        return max(grid_width, min_width), height

    def draw(self, screen, top_left, item_filter, label=None):
        x, y = top_left

        if label:
            label_surf = self.label_font.render(label, True, "#000000")
            screen.blit(label_surf, (x, y))
            y += label_surf.get_height() + 6

        self.checkbox_rect = py.Rect(x, y, self.CHECKBOX_SIZE, self.CHECKBOX_SIZE)
        py.draw.rect(screen, "#FFFFFF", self.checkbox_rect)
        py.draw.rect(screen, "#333333", self.checkbox_rect, 2)
        if item_filter.enabled:
            py.draw.rect(screen, "#3A7D44", self.checkbox_rect.inflate(-6, -6))

        checkbox_label = self.checkbox_font.render("Filter enabled", True, "#000000")
        screen.blit(checkbox_label, (self.checkbox_rect.right + 8, self.checkbox_rect.y + 2))

        grid_top = y + self.CHECKBOX_SIZE + 8
        self._draw_slots(screen, (x, grid_top), item_filter)

    def _draw_slots(self, screen, top_left, item_filter):
        self.slot_rects = []
        enabled = item_filter.enabled

        for index in range(ItemFilter.SLOT_COUNT):
            rect = _grid_cell_rect(top_left, index, self.columns)
            item_id = item_filter.slots[index]

            bg_color = "#BFE3C4" if (enabled and item_id) else "#E5E5E5"
            py.draw.rect(screen, bg_color, rect)
            py.draw.rect(screen, "#888888", rect, 2)

            if item_id:
                item = get_item_by_id(item_id)
                if item and item.sprite:
                    size = rect.width - 6
                    img = item.get_scaled_sprite(size)
                    if img:
                        if not enabled:
                            img = img.copy()
                            img.set_alpha(100)
                        screen.blit(img, (rect.x + 3, rect.y + 3))

            self.slot_rects.append((rect, index))

    def handle_click(self, mx, my, item_filter, right_click=False):
        """Returns True if the click landed on one of this panel's own
        widgets (so the caller knows not to treat it as a click-outside)."""
        if self.checkbox_rect and self.checkbox_rect.collidepoint(mx, my):
            if not right_click:
                item_filter.enabled = not item_filter.enabled
            return True

        if not item_filter.enabled:
            return False

        for rect, index in self.slot_rects:
            if rect.collidepoint(mx, my):
                if right_click:
                    item_filter.clear_slot(index)
                elif self.on_slot_click:
                    self.on_slot_click(item_filter, index)
                return True

        return False


class ItemPickerOverlay:
    """A grid listing every item in the game, drawn in its own reserved
    area - always to the right of a filter panel's slots, never on top of
    them - shared by however many ItemFilterPanels sit in the same owning
    UI (a splitter's three side panels all pop the same picker into the
    same spot). Opened via ItemFilterPanel's on_slot_click callback;
    picking an item assigns it into whichever (ItemFilter, slot_index) is
    currently targeted and closes the picker. Right-click, or a click that
    misses every item cell, cancels without assigning."""

    COLUMNS = 4

    def __init__(self):
        self.target = None  # (item_filter, slot_index) or None
        self.item_rects = []
        self.bounds = None

        self.title_font = py.font.SysFont("Arial", 15, bold=True)

    @property
    def is_open(self):
        return self.target is not None

    def open_for(self, item_filter, slot_index):
        self.target = (item_filter, slot_index)

    def close(self):
        self.target = None
        self.item_rects = []
        self.bounds = None

    def content_size(self):
        grid_width, grid_height = _grid_size(len(ITEMS), self.COLUMNS)
        title_height = self.title_font.get_height() + 6
        return grid_width, title_height + grid_height

    def draw(self, screen, top_left):
        self.item_rects = []
        self.bounds = None

        if not self.is_open:
            return

        x, y = top_left
        title = self.title_font.render("Choose an item", True, "#000000")
        screen.blit(title, (x, y))
        grid_top = (x, y + title.get_height() + 6)

        for i, item in enumerate(ITEMS):
            rect = _grid_cell_rect(grid_top, i, self.COLUMNS)
            py.draw.rect(screen, "#FFF3C4", rect)
            py.draw.rect(screen, "#886F00", rect, 2)

            if item.sprite:
                size = rect.width - 6
                img = item.get_scaled_sprite(size)
                if img:
                    screen.blit(img, (rect.x + 3, rect.y + 3))

            self.item_rects.append((rect, item))

        grid_width, grid_height = _grid_size(len(ITEMS), self.COLUMNS)
        self.bounds = py.Rect(grid_top[0], grid_top[1], grid_width, grid_height)

    def handle_click(self, mx, my, right_click=False):
        """Returns True if the click was consumed by the picker (whether
        or not it actually picked an item)."""
        if not self.is_open:
            return False

        if right_click:
            self.close()
            return True

        item_filter, slot_index = self.target

        for rect, item in self.item_rects:
            if rect.collidepoint(mx, my):
                if item.item_id not in item_filter.slots:
                    item_filter.set_slot(slot_index, item.item_id)
                self.close()
                return True

        if self.bounds and self.bounds.collidepoint(mx, my):
            # Inside the picker's grid area but not on an item cell (a gap,
            # if the item count isn't a multiple of COLUMNS) - dismiss
            # without assigning, but still consume the click.
            self.close()
            return True

        # Click landed somewhere else entirely - close the picker but
        # don't consume the click, so the caller can still route it
        # normally (e.g. to a slot click, or the outer UI's
        # click-outside-closes check).
        self.close()
        return False
