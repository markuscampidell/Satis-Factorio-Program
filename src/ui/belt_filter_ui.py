# ui.belt_filter_ui
import pygame as py

from ui.item_filter_panel import ItemFilterPanel, ItemPickerOverlay


class BeltFilterUI:
    """State and interaction (open/close, filter ticking/item picking) for
    a belt segment's filter panel - always centered on screen while open,
    same open/close/auto-close pattern as StorageUI/ProducingMachineUI.
    Drawing lives in BeltFilterUIRenderer."""

    PADDING = 16
    TITLE_HEIGHT = 40
    PICKER_GAP = 20

    def __init__(self, camera, player_inventory_ui, panel_side="right"):
        self.picker = ItemPickerOverlay()
        self.panel = ItemFilterPanel(columns=5, on_slot_click=self.picker.open_for)

        content_w, content_h = self.panel.content_size(with_label=False)
        picker_w, picker_h = self.picker.content_size()
        self.slot_area_width = content_w

        self.width = content_w + self.PICKER_GAP + picker_w + self.PADDING * 2
        self.height = self.TITLE_HEIGHT + max(content_h, picker_h) + self.PADDING

        self.sprite = py.Surface((self.width, self.height), py.SRCALPHA)
        py.draw.rect(self.sprite, "#CAC8E4", self.sprite.get_rect(), border_radius=18)
        self.sprite.set_alpha(220)
        self.rect = self.sprite.get_rect(center=(camera.screen_width // 2, camera.screen_height // 2))

        self.open = False
        self.selected_belt = None

        self.camera = camera
        self.player_inventory_ui = player_inventory_ui
        self.panel_side = panel_side

    def handle_event(self, event, just_placed, placing_machine):
        if placing_machine or just_placed:
            return
        if event.type == py.VIDEORESIZE:
            return

        mx, my = getattr(event, "pos", (None, None))
        is_mouse_down = event.type == py.MOUSEBUTTONDOWN
        left_click = is_mouse_down and getattr(event, "button", None) == 1
        right_click = is_mouse_down and getattr(event, "button", None) == 3

        if self.open and self.selected_belt:
            if (left_click or right_click) and mx is not None:
                if self.picker.is_open:
                    self.picker.handle_click(mx, my, right_click=right_click)
                else:
                    self.panel.handle_click(mx, my, self.selected_belt.filter, right_click=right_click)
            self._handle_close_click(left_click, mx, my)
            self._handle_visibility()

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
        if not self.selected_belt:
            return
        viewport = py.Rect(0, 0, self.camera.screen_width, self.camera.screen_height)
        if not viewport.colliderect(self.selected_belt.rect.move(-self.camera.x, -self.camera.y)):
            self.close()

    def close(self):
        self.open = False
        self.selected_belt = None
        self.picker.close()

    def open_for(self, belt_segment):
        self.open = True
        self.selected_belt = belt_segment
