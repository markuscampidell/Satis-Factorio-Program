# ui.producing_machine_ui
import pygame as py


class ProducingMachineUI:
    """State and interaction (open/close, recipe/close clicks) for a
    producing machine's panel - always centered on screen while open.
    Drawing lives in MachineUIRenderer."""

    def __init__(self, camera, world, player, player_inventory_ui, screen, panel_side="right"):
        self.sprite = py.Surface((400, 300), py.SRCALPHA)
        self.rect = self.sprite.get_rect(center=(camera.screen_width // 2, camera.screen_height // 2))
        # Draw rounded panel background
        py.draw.rect(self.sprite, "#CAC8E4", self.sprite.get_rect(), border_radius=18)
        self.open = False
        self.selected_machine = None

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
        """Handle mouse events for recipe selection and closing the UI."""
        if placing_machine or just_placed: return

        # Resizing the window shouldn't count as "walked away from the
        # machine" - the panel is always centered now, not tied to the
        # machine's on-screen position, so only real player movement
        # should be able to trigger the visibility auto-close below.
        if event.type == py.VIDEORESIZE: return

        mx, my = getattr(event, "pos", (None, None))
        left_click = event.type == py.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1
        if self.open and self.selected_machine:
            self._handle_recipe_click(left_click, mx, my)
            self._handle_close_click(left_click, mx, my)
            self._handle_visibility()

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
        # Built from the camera's live size rather than a cached Surface -
        # game.py reassigns the screen to a new Surface on every resize, so
        # a Surface captured once at construction goes stale and its
        # .get_rect() no longer matches the real window, which was
        # incorrectly closing this UI on every resize.
        viewport = py.Rect(0, 0, self.camera.screen_width, self.camera.screen_height)
        if not viewport.colliderect(self.selected_machine.rect.move(-self.camera.x, -self.camera.y)):
            self.close()

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
