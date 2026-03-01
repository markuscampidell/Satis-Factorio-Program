# ui.hand_crafting_ui
import pygame as py

from ui.recipe_ui import RecipeUI
from constants.itemdata import get_item_by_id


class HandCraftingUI:

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

        self.font = py.font.SysFont("Arial", 20)
        self.small_font = py.font.SysFont("Arial", 16)

        self.progress = 0.0
        self.crafting_mode = None

        self.recipe_rects = []
        self.produce_button_rect = None
        self.cancel_button_rect = None

        # Hover
        self._hovered_recipe = None
        self._hover_panel_visible = False
        self.recipe_ui = RecipeUI()

    def draw(self, screen):
        if not self.open: return

        w, h = self.get_screen_size()

        # Always stick to right side, vertically centered
        self.rect.x = w - self.width - 20
        self.rect.y = h // 2 - self.height // 2

        screen.blit(self.sprite, self.rect)

        self._draw_recipes(screen)
        self._draw_selected_recipe_panel(screen)
        self._draw_produce_button(screen)
        self._draw_progress_bar(screen)
        self._draw_cancel_button(screen)

        self._update_hover(screen)

    def _draw_selected_recipe_panel(self, screen):
        recipe = self.player.handcrafting.get_selected_recipe()
        if not recipe: return

        panel_rect = py.Rect(self.rect.x + 20, self.rect.bottom - 320, self.width - 40, 180)

        self.recipe_ui.draw_recipe_panel(screen, recipe, custom_rect=panel_rect)

    def _draw_recipes(self, screen):
        self.recipe_rects = []
        y = self.rect.y + 40

        # Header
        header = self.font.render("Handcrafting", True, "#000000")
        screen.blit(header, (self.rect.x + 10, self.rect.y + 10))

        for i, recipe in enumerate(self.player.handcrafting.recipes):
            r = py.Rect(self.rect.x + 10, y, self.width - 20, 40)
            self.recipe_rects.append((r, recipe))

            # Highlight selected recipe
            if i == self.player.handcrafting.selected_recipe_index:
                py.draw.rect(screen, (255, 165, 0), r, border_radius=6)

            # Draw recipe name
            text = self.font.render(recipe.name, True, "#000000")
            screen.blit(text, (r.x + 10, r.y + 8))

            # Draw output item sprites
            output_x = r.x + 150  # start drawing outputs 150px from left
            for item_id in recipe.outputs.keys():
                item = get_item_by_id(item_id)
                if item and item.sprite:
                    sprite = py.transform.scale(item.sprite, (24, 24))
                    screen.blit(sprite, (output_x, r.y + 8))
                    output_x += 28  # move to the right for next sprite

            y += 45  # spacing between recipes

    def _draw_produce_button(self, screen):
        recipe = self.player.handcrafting.get_selected_recipe()
        can_craft = recipe and self.player.handcrafting.inventory.has_enough_items(recipe.inputs)

        button_w, button_h = 180, 40
        producing = self.crafting_mode is not None

        if producing and can_craft:
            button_w = int(button_w * 0.95)
            button_h = int(button_h * 0.95)
            color = (0, 180, 0)
        else:
            color = (0, 230, 0) if can_craft else (120, 120, 120)

        button_x = self.rect.centerx - button_w // 2
        button_y = self.rect.bottom - 120

        self.produce_button_rect = py.Rect(button_x, button_y, button_w, button_h)
        py.draw.rect(screen, color, self.produce_button_rect, border_radius=12)

        text = self.font.render("Produce", True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=self.produce_button_rect.center))

    def _draw_progress_bar(self, screen):
        bar_w, bar_h = 180, 20
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.bottom - 65

        bg = py.Rect(bar_x, bar_y, bar_w, bar_h)
        py.draw.rect(screen, "#9A98B5", bg, border_radius=6)

        fill = py.Rect(bar_x, bar_y, int(bar_w * self.progress), bar_h)
        py.draw.rect(screen, (0, 230, 0), fill, border_radius=6)

    def _draw_cancel_button(self, screen):
        # Base size
        normal_w, normal_h = 80, 20

        if self.crafting_mode is None:
            # Smaller and darker
            cancel_w = int(normal_w * 0.9)
            cancel_h = int(normal_h * 0.9)
            color = (120, 0, 0)
        else:
            # Normal size and color
            cancel_w = normal_w
            cancel_h = normal_h
            color = (200, 0, 0)

        cancel_x = self.rect.centerx - cancel_w // 2
        cancel_y = self.rect.bottom - 30

        self.cancel_button_rect = py.Rect(cancel_x, cancel_y, cancel_w, cancel_h)
        py.draw.rect(screen, color, self.cancel_button_rect, border_radius=8)

        text = self.font.render("Cancel", True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=self.cancel_button_rect.center))

    def _update_hover(self, screen):
        mx, my = py.mouse.get_pos()
        hovered = None

        for rect, recipe in self.recipe_rects:
            if rect.collidepoint(mx, my):
                hovered = recipe
                break

        if hovered != self._hovered_recipe:
            self._hovered_recipe = hovered
            self._hover_panel_visible = bool(hovered)

        if self._hover_panel_visible:
            self.recipe_ui.draw_recipe_panel(screen, self._hovered_recipe, self.rect, self.panel_side)

    def handle_mouse(self, event):
        if not self.open: return

        # Left click
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Produce: only one craft
            if self.produce_button_rect.collidepoint(pos):
                recipe = self.player.handcrafting.get_selected_recipe()
                if recipe and self.player.handcrafting.inventory.has_enough_items(recipe.inputs):
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
                    self.progress = 0.0
                    return
                
    def update(self, dt):
        if not self.open: return

        recipe = self.player.handcrafting.get_selected_recipe()
        if not recipe:
            self.progress = 0.0
            return

        can_craft = self.player.handcrafting.inventory.has_enough_items(recipe.inputs)
        process_time = getattr(recipe, "process_time", 1)
        producing = self.crafting_mode is not None

        if not producing: return

        if not can_craft:
            self.crafting_mode = None
            self.progress = 0.0
            return

        self.progress += dt / process_time

        if self.progress >= 1.0:
            self.player.handcrafting.try_craft_selected()
            self.progress = 0.0

            if self.crafting_mode == "single":
                self.crafting_mode = None

    def close(self):
        self.open = False
        self.crafting_mode = None
        self.progress = 0.0