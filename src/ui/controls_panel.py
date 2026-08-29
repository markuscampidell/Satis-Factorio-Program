# ui.controls_panel
import pygame as py

from ui.scroll import clamp_scroll, apply_wheel_scroll, draw_scrollbar

CONTROL_SECTIONS = [
    ("Movement", [
        ("W / A / S / D, Arrow Keys", "Move around"),
    ]),
    ("Menus (ESC)", [
        ("ESC", "Open the Game Menu - or close whatever panel is currently open"),
        ("TAB", "Toggle your inventory"),
        ("F", "Toggle the hand-crafting panel"),
    ]),
    ("Building", [
        ("Q", "Toggle build mode"),
        ("X", "Toggle delete mode"),
        ("1 - 5", "Pick what to build: Smelter, Assembler, Belt, Splitter, Storage"),
        ("R", "Rotate the selected building clockwise"),
        ("Shift + R", "Rotate the selected building counter-clockwise"),
        ("T", "Rotate the selected building 180 degrees"),
        ("Left Click", "Place the selected building - or delete under the cursor in delete mode"),
        ("Shift + Left Click", "In delete mode, delete an entire connected belt run at once"),
        ("Right Click", "Cancel the current placement, or exit build/delete mode"),
    ]),
    ("Crafting", [
        ("Left Click", "Select a recipe, or press Produce/Cancel"),
        ("SPACE", "Toggle auto-craft for the selected recipe"),
    ]),
    ("Inventory & Storage", [
        ("Left Click", "Open a machine's or storage's panel by clicking its tile"),
        ("Shift + Left Click", "Move one stack between the open panel and your inventory"),
        ("Ctrl + Left Click", "Move every stack of that item type between the open panel and your inventory"),
        ("Left Click (outside a panel)", "Close that panel"),
        ("Scroll Wheel", "Scroll a panel's contents, like this one"),
    ]),
    ("Temporary", [
        ("I", "Instantly fill a selected machine's recipe inputs, while its panel is open (debug)"),
    ]),
]


class ControlsPanel:
    """"Controls" help overlay: every key/mouse control, grouped under
    headings, in a scrollable panel. Opened by GameMenuBar; closes itself
    on ESC, the x button, or a click outside the panel - handle_event
    returns True the frame that happens."""

    WIDTH = 560
    MAX_HEIGHT = 560
    PADDING = 24
    LINE_SPACING = 6
    ENTRY_GAP = 10
    HEADER_GAP_BEFORE = 20
    HEADER_GAP_AFTER = 10
    SCROLL_SPEED = 40

    def __init__(self):
        self.open = False
        self.title_font = py.font.SysFont("Arial", 26, bold=True)
        self.header_font = py.font.SysFont("Arial", 20, bold=True)
        self.key_font = py.font.SysFont("Arial", 18, bold=True)
        self.desc_font = py.font.SysFont("Arial", 18)
        self.row_height = max(self.key_font.get_height(), self.desc_font.get_height())

        self.box_rect = None
        self.close_rect = None
        self.viewport_rect = None
        self.scroll_offset = 0
        self._content_height = 0
        self._layout = None
        self._layout_width = None

    def open_panel(self):
        self.open = True
        self.scroll_offset = 0

    def handle_event(self, event):
        if not self.open:
            return False

        if event.type == py.KEYDOWN and event.key == py.K_ESCAPE:
            self.open = False
            return True

        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect and self.close_rect.collidepoint(event.pos):
                self.open = False
                return True
            if self.box_rect and not self.box_rect.collidepoint(event.pos):
                self.open = False
                return True
            return False

        if event.type == py.MOUSEWHEEL and self.box_rect and self.box_rect.collidepoint(py.mouse.get_pos()):
            self.scroll_offset = apply_wheel_scroll(
                self.scroll_offset, event, self._content_height, self.viewport_rect.height, self.SCROLL_SPEED)
            return True

        return False

    def draw(self, screen):
        if not self.open:
            return

        w, h = screen.get_size()
        box = py.Rect(0, 0, self.WIDTH, min(self.MAX_HEIGHT, h - 80))
        box.center = (w // 2, h // 2)
        self.box_rect = box

        py.draw.rect(screen, (240, 240, 240), box, border_radius=10)
        py.draw.rect(screen, (60, 60, 60), box, width=2, border_radius=10)

        title = self.title_font.render("Controls", True, (0, 0, 0))
        screen.blit(title, title.get_rect(midtop=(box.centerx, box.y + 14)))

        self.close_rect = py.Rect(0, 0, 28, 28)
        self.close_rect.topright = (box.right - 10, box.y + 10)
        py.draw.rect(screen, (150, 0, 0), self.close_rect, border_radius=6)
        x_text = self.header_font.render("x", True, "#FFFFFF")
        screen.blit(x_text, x_text.get_rect(center=self.close_rect.center))

        content_top = box.y + 60
        viewport = py.Rect(box.x + self.PADDING, content_top,
                            box.width - self.PADDING * 2, box.bottom - self.PADDING - content_top)
        self.viewport_rect = viewport

        self._ensure_layout(viewport.width)
        self.scroll_offset = clamp_scroll(self.scroll_offset, self._content_height, viewport.height)

        prev_clip = screen.get_clip()
        screen.set_clip(viewport)

        y = viewport.y - self.scroll_offset
        for kind, *rest in self._layout:
            if kind == "header":
                text, height = rest
                if y + height >= viewport.y and y <= viewport.bottom:
                    surf = self.header_font.render(text, True, (40, 40, 90))
                    screen.blit(surf, (viewport.x, y))
                y += height
            else:  # "entry"
                rows, height = rest
                if y + height >= viewport.y and y <= viewport.bottom:
                    row_y = y
                    for surf in rows:
                        screen.blit(surf, (viewport.x, row_y))
                        row_y += self.row_height + self.LINE_SPACING
                y += height

        screen.set_clip(prev_clip)

        if self._content_height > viewport.height:
            track = py.Rect(viewport.right + 6, viewport.y, 6, viewport.height)
            draw_scrollbar(screen, track, self.scroll_offset, self._content_height, viewport.height)

    def _ensure_layout(self, width):
        if self._layout is not None and self._layout_width == width:
            return

        self._layout_width = width
        layout = []
        y = 0

        for i, (heading, entries) in enumerate(CONTROL_SECTIONS):
            if i > 0:
                y += self.HEADER_GAP_BEFORE
            header_h = self.header_font.get_height()
            layout.append(("header", heading, header_h))
            y += header_h + self.HEADER_GAP_AFTER

            for key_text, desc_text in entries:
                rows = self._render_entry(key_text, desc_text, width)
                entry_h = len(rows) * (self.row_height + self.LINE_SPACING) + self.ENTRY_GAP
                layout.append(("entry", rows, entry_h))
                y += entry_h

        self._layout = layout
        self._content_height = y

    def _render_entry(self, key_text, desc_text, width):
        """Renders "Key: description" as a list of full-width row surfaces
        stacked vertically - the key sits on the first row, and the
        description word-wraps onto as many rows as it needs, indented so
        wrapped lines line up under the description rather than the key.
        Keeps every line readable regardless of panel width."""
        key_surf = self.key_font.render(key_text + ":", True, (15, 15, 60))
        indent = key_surf.get_width() + 10

        wrapped = self._wrap_text(desc_text, self.desc_font, max(40, width - indent))

        rows = []
        first_row = py.Surface((width, self.row_height), py.SRCALPHA)
        first_row.blit(key_surf, (0, 0))
        if wrapped:
            first_row.blit(self.desc_font.render(wrapped[0], True, (0, 0, 0)), (indent, 0))
        rows.append(first_row)

        for line in wrapped[1:]:
            row = py.Surface((width, self.row_height), py.SRCALPHA)
            row.blit(self.desc_font.render(line, True, (0, 0, 0)), (indent, 0))
            rows.append(row)

        return rows

    def _wrap_text(self, text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
