# ui.producing_machine_ui
import pygame as py


class ProducingMachineUI:
    """State and interaction (open/close, dragging, recipe/close clicks) for
    a producing machine's panel. Drawing lives in ProducingMachineRenderer."""

    def __init__(self, camera, world, player, player_inventory_ui, screen, panel_side="right"):
        self.sprite = py.Surface((500, 300), py.SRCALPHA)
        self.rect = self.sprite.get_rect(center=(camera.screen_width // 2, camera.screen_height // 2))
        # Draw rounded panel background
        py.draw.rect(self.sprite, "#CAC8E4", self.sprite.get_rect(), border_radius=18)
        self.open = False
        self.selected_machine = None
        self.dragging = False
        self.drag_offset = (0, 0)

        self.slot_rects = []
        self.recipe_rects = []
        self.sprite.set_alpha(220)
        self.world = world
        self.camera = camera
        self.player = player
        self.player_inventory_ui = player_inventory_ui
        self.screen = screen

        self.panel_side = panel_side

    def handle_event(self, event, just_placed, placing_machine):
        """Handle mouse events for dragging, recipe selection, and closing UI."""
        if placing_machine or just_placed: return

        mx, my = getattr(event, "pos", (None, None))
        left_click = event.type == py.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1
        self._handle_drag(event, mx, my)
        if self.open and self.selected_machine:
            self._handle_recipe_click(left_click, mx, my)
            self._handle_close_click(left_click, mx, my)
            self._handle_visibility()

    def _handle_drag(self, event, mx, my):
        if mx is None or my is None:
            return
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mx, my) and not any(r.collidepoint(mx, my) for r in self.slot_rects):
                self.dragging = True
                self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        elif event.type == py.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == py.MOUSEMOTION and self.dragging:
            self.rect.topleft = (mx - self.drag_offset[0], my - self.drag_offset[1])

    def _handle_recipe_click(self, left_click, mx, my):
        if not left_click:
            return
        if mx is not None and my is not None:
            for rect, recipe in self.recipe_rects:
                if rect.collidepoint(mx, my):
                    self.selected_machine.set_recipe(recipe, player_inventory=self.player.inventory)
                    break

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
        if not self.selected_machine:
            return
        if not self.screen.get_rect().colliderect(self.selected_machine.rect.move(-self.camera.x, -self.camera.y)):
            self.close()
            self.rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)

    def close(self):
        """Closes the UI and deselects the machine."""
        self.open = False
        self.selected_machine = None

    def open_for(self, machine):
        """Opens the UI for a specific machine."""
        self.open = True
        self.selected_machine = machine

    def update_size(self, width, height):
        self.width = width
        self.height = height
