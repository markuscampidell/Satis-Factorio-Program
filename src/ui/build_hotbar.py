# ui.build_hotbar
import pygame as py

from objects.machines.smelter import Smelter
from objects.machines.assembler import Assembler
from objects.machines.splitter import Splitter
from objects.machines.storage import Storage
from objects.conveyors.belt_segment import BeltSegment

BELT_ICON_PATH = "src/assets/sprites/conveyors/straight/belt_straight_right.png"

# Ordered slot definitions - (key, kind, payload). kind is one of
# "none" | "machine" | "delete". Index in this list (+1) is both the
# number key that selects it and the label drawn on the slot, so this one
# list is the single source of truth for the 1-7 hotbar layout.
SLOT_DEFS = [
    (py.K_1, "machine", Smelter),
    (py.K_2, "machine", Assembler),
    (py.K_3, "machine", BeltSegment),
    (py.K_4, "machine", Splitter),
    (py.K_5, "machine", Storage),
    (py.K_6, "none", None),
    (py.K_7, "delete", None),
]


class BuildHotbar:
    """Always-visible, always-clickable row of slots at the bottom-middle
    of the screen: "Nothing", each buildable machine, and "Delete" - a
    direct readout and selector for BuildSystem.build_mode /
    selected_machine_class. Selecting a slot (by number key 1-7 or by
    clicking it) closes any open UI panel first, exactly like the existing
    X (delete-toggle) key already does, so the hotbar always works
    regardless of what else is open."""

    SLOT_SIZE = 56
    GAP = 8
    MARGIN_BOTTOM = 18

    def __init__(self, build_system, ui_manager):
        self.build_system = build_system
        self.ui_manager = ui_manager
        self.key_font = py.font.SysFont("Arial", 13, bold=True)
        self._icons = self._load_icons()
        self.slot_rects = []  # [(rect, kind, payload)] - populated each draw

    def _load_icons(self):
        icons = {}
        for _key, kind, payload in SLOT_DEFS:
            if kind != "machine":
                continue
            path = BELT_ICON_PATH if payload is BeltSegment else payload.SPRITE_PATH
            image = py.image.load(path).convert_alpha()
            icons[payload] = py.transform.scale(image, (self.SLOT_SIZE - 16, self.SLOT_SIZE - 16))
        return icons

    def _current_selection(self):
        bs = self.build_system
        if bs.build_mode == "deleting":
            return "delete", None
        if bs.build_mode == "building":
            return "machine", bs.selected_machine_class
        return "none", None

    def handle_event(self, event):
        """Returns True if the event selected a slot and should not
        propagate any further this frame."""
        if event.type == py.KEYDOWN:
            for key, kind, payload in SLOT_DEFS:
                if event.key == key:
                    self._activate(kind, payload)
                    return True
            return False

        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            for rect, kind, payload in self.slot_rects:
                if rect.collidepoint(event.pos):
                    self._activate(kind, payload)
                    return True

        return False

    def _activate(self, kind, payload):
        self.ui_manager.close_all_uis()
        if kind == "none":
            self.build_system.reset_build_state()
        elif kind == "machine":
            self.build_system.select_machine(payload)
            self.build_system.reset_rotation()
        elif kind == "delete":
            self.build_system.toggle_delete_mode()

    def draw(self, screen):
        w, h = screen.get_size()
        n = len(SLOT_DEFS)
        total_w = n * self.SLOT_SIZE + (n - 1) * self.GAP
        start_x = w // 2 - total_w // 2
        y = h - self.SLOT_SIZE - self.MARGIN_BOTTOM

        active_kind, active_payload = self._current_selection()
        self.slot_rects = []

        for i, (_key, kind, payload) in enumerate(SLOT_DEFS):
            rect = py.Rect(start_x + i * (self.SLOT_SIZE + self.GAP), y, self.SLOT_SIZE, self.SLOT_SIZE)
            self.slot_rects.append((rect, kind, payload))

            is_active = kind == active_kind and (kind != "machine" or payload is active_payload)

            bg = (255, 195, 60) if is_active else (55, 55, 55)
            py.draw.rect(screen, bg, rect, border_radius=8)
            py.draw.rect(screen, (20, 20, 20), rect, width=2, border_radius=8)

            self._draw_slot_icon(screen, rect, kind, payload)

            key_label = self.key_font.render(str(i + 1), True, "#FFFFFF")
            screen.blit(key_label, (rect.x + 4, rect.y + 2))

    def _draw_slot_icon(self, screen, rect, kind, payload):
        if kind == "machine":
            icon = self._icons.get(payload)
            if icon:
                screen.blit(icon, icon.get_rect(center=rect.center))
            return

        if kind == "none":
            inner = rect.inflate(-18, -18)
            py.draw.rect(screen, (170, 170, 170), inner, width=2, border_radius=4)
            return

        # kind == "delete" - a plain trash-can glyph drawn from primitives,
        # since there's no sprite asset for "delete" the way there is for
        # every buildable machine.
        body = py.Rect(0, 0, rect.width - 26, rect.height - 28)
        body.center = (rect.centerx, rect.centery + 5)
        py.draw.rect(screen, (220, 70, 70), body, border_radius=3)
        for lx in range(body.left + 6, body.right - 5, 6):
            py.draw.line(screen, (150, 30, 30), (lx, body.top + 4), (lx, body.bottom - 4), 2)

        lid = py.Rect(0, 0, rect.width - 16, 6)
        lid.center = (rect.centerx, body.top - 2)
        py.draw.rect(screen, (220, 70, 70), lid, border_radius=2)
        handle = py.Rect(0, 0, 14, 5)
        handle.center = (rect.centerx, lid.top - 2)
        py.draw.rect(screen, (220, 70, 70), handle, border_radius=2)
