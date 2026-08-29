# ui.hand_crafting_ui
import pygame as py

from ui.scroll import apply_wheel_scroll


class HandCraftingUI:
    """State and interaction (open/close, crafting progress, button clicks)
    for the handcrafting panel. Drawing lives in HandCraftingRenderer."""

    SCROLL_SPEED = 40

    def __init__(self, player, get_screen_size, panel_side="left"):
        self.player = player
        self.get_screen_size = get_screen_size
        self.open = False
        self.panel_side = panel_side

        self.width = 300
        self.height = 600

        self.sprite = py.Surface((self.width, self.height), py.SRCALPHA)
        py.draw.rect(self.sprite, (202, 200, 228, 220), self.sprite.get_rect(), border_radius=18)

        w, h = self.get_screen_size()
        self.rect = self.sprite.get_rect(x=w - self.width, y=h // 2 - self.height // 2)

        self.progress = 0.0
        self.crafting_mode = None

        self.recipe_rects = []
        self.produce_button_rect = None
        self.cancel_button_rect = None
        self.recipe_list_viewport = None  # set by the renderer each draw
        self.recipe_list_content_height = 0
        self.scroll_offset = 0

    def handle_mouse(self, event):
        if not self.open: return

        if event.type == py.MOUSEWHEEL and self.recipe_list_viewport and self.recipe_list_viewport.collidepoint(py.mouse.get_pos()):
            self.scroll_offset = apply_wheel_scroll(
                self.scroll_offset, event, self.recipe_list_content_height,
                self.recipe_list_viewport.height, self.SCROLL_SPEED)
            return

        # Left click
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Produce: only one craft
            if self.produce_button_rect.collidepoint(pos):
                recipe = self.player.handcrafting.get_selected_recipe()
                if recipe and self.player.handcrafting.check_craft_status(recipe) == "ok":
                    self.crafting_mode = "single"
                    self.progress = 0.0
                return

            # Cancel
            if self.cancel_button_rect and self.cancel_button_rect.collidepoint(pos):
                self.crafting_mode = None
                self.progress = 0.0
                return

            # Select recipe
            for i, (rect, recipe) in enumerate(self.recipe_rects):
                if rect.collidepoint(pos):
                    self.player.handcrafting.selected_recipe_index = i
                    self.crafting_mode = None
                    self.progress = 0.0
                    return

    def update(self, dt):
        if not self.open: return

        if self.crafting_mode is None:
            self.progress = 0.0
            return

        recipe = self.player.handcrafting.get_selected_recipe()
        if not recipe:
            self.progress = 0.0
            return

        process_time = getattr(recipe, "process_time", 1)

        # Stops producing the moment inputs run out *or* the output
        # wouldn't fit in the inventory, instead of losing items silently.
        if self.player.handcrafting.check_craft_status(recipe) != "ok":
            self.crafting_mode = None
            self.progress = 0.0
            return

        self.progress += dt / process_time

        # A loop (not just `if`) so a short process_time relative to dt can
        # complete more than once in a frame, and a tiny epsilon so float
        # accumulation error can't stall a completion that's already due.
        while self.crafting_mode is not None and self.progress >= 1.0 - 1e-9:
            self.player.handcrafting.try_craft_selected()
            leftover = max(0.0, self.progress - 1.0)

            if self.crafting_mode == "single":
                self.crafting_mode = None
                self.progress = 0.0
                break

            # auto mode: carry the overshoot into the next craft instead of
            # discarding it, but only if it can start right away - same
            # reasoning as ProducingMachine._update_processing.
            recipe = self.player.handcrafting.get_selected_recipe()
            if not recipe or self.player.handcrafting.check_craft_status(recipe) != "ok":
                self.crafting_mode = None
                self.progress = 0.0
                break

            process_time = getattr(recipe, "process_time", 1)
            self.progress = leftover

    def close(self):
        self.open = False
        self.crafting_mode = None
        self.progress = 0.0
