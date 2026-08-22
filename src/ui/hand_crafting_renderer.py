# ui.hand_crafting_renderer
import pygame as py

from ui.recipe_ui import RecipeUI
from constants.itemdata import get_item_by_id


class HandCraftingRenderer:
    """Draws a HandCraftingUI's panel: recipe list, produce/cancel buttons,
    progress bar, hover panel. Reads/writes the UI's rect and hit-test rects."""

    def __init__(self, hand_crafting_ui):
        self.ui = hand_crafting_ui
        self.font = py.font.SysFont("Arial", 20)
        self.small_font = py.font.SysFont("Arial", 16)
        self.recipe_ui = RecipeUI()

        # Hover
        self._hovered_recipe = None
        self._hover_panel_visible = False

    def draw(self, screen):
        ui = self.ui
        if not ui.open: return

        w, h = ui.get_screen_size()

        # Always stick to right side, vertically centered
        ui.rect.x = w - ui.width #- 20
        ui.rect.y = h // 2 - ui.height // 2

        screen.blit(ui.sprite, ui.rect)

        self._draw_recipes(screen)
        self._draw_selected_recipe_panel(screen)
        self._draw_produce_button(screen)
        self._draw_progress_bar(screen)
        self._draw_cancel_button(screen)

        self._update_hover(screen)

    def _draw_selected_recipe_panel(self, screen):
        ui = self.ui
        recipe = ui.player.handcrafting.get_selected_recipe()
        if not recipe: return

        panel_rect = py.Rect(ui.rect.x + 20, ui.rect.bottom - 320, ui.width - 40, 180)

        self.recipe_ui.draw_recipe_panel(screen, recipe, custom_rect=panel_rect)

    def _draw_recipes(self, screen):
        ui = self.ui
        ui.recipe_rects = []
        y = ui.rect.y + 40

        # Header
        header = self.font.render("Handcrafting", True, "#000000")
        screen.blit(header, (ui.rect.x + 10, ui.rect.y + 10))

        for i, recipe in enumerate(ui.player.handcrafting.recipes):
            r = py.Rect(ui.rect.x + 10, y, ui.width - 20, 40)
            ui.recipe_rects.append((r, recipe))

            # Highlight selected recipe
            if i == ui.player.handcrafting.selected_recipe_index:
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
        ui = self.ui
        recipe = ui.player.handcrafting.get_selected_recipe()
        status = ui.player.handcrafting.check_craft_status(recipe) if recipe else "no_inputs"
        can_craft = status == "ok"

        button_w, button_h = 180, 40
        producing = ui.crafting_mode is not None

        if producing and can_craft:
            button_w = int(button_w * 0.95)
            button_h = int(button_h * 0.95)
            color = (0, 180, 0)
        elif can_craft:
            color = (0, 230, 0)
        elif status == "no_space":
            # Inputs are there, but the output wouldn't fit - matches the
            # orange "not enough inventory space" indicator used elsewhere.
            color = (255, 165, 0)
        else:
            color = (120, 120, 120)

        button_x = ui.rect.centerx - button_w // 2
        button_y = ui.rect.bottom - 120

        ui.produce_button_rect = py.Rect(button_x, button_y, button_w, button_h)
        py.draw.rect(screen, color, ui.produce_button_rect, border_radius=12)

        text = self.font.render("Produce", True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=ui.produce_button_rect.center))

    def _draw_progress_bar(self, screen):
        ui = self.ui
        bar_w, bar_h = 180, 20
        bar_x = ui.rect.centerx - bar_w // 2
        bar_y = ui.rect.bottom - 65

        bg = py.Rect(bar_x, bar_y, bar_w, bar_h)
        py.draw.rect(screen, "#9A98B5", bg, border_radius=6)

        fill = py.Rect(bar_x, bar_y, int(bar_w * ui.progress), bar_h)
        py.draw.rect(screen, (0, 230, 0), fill, border_radius=6)

    def _draw_cancel_button(self, screen):
        ui = self.ui
        # Base size
        normal_w, normal_h = 80, 20

        if ui.crafting_mode is None:
            # Smaller and darker
            cancel_w = int(normal_w * 0.9)
            cancel_h = int(normal_h * 0.9)
            color = (120, 0, 0)
        else:
            # Normal size and color
            cancel_w = normal_w
            cancel_h = normal_h
            color = (200, 0, 0)

        cancel_x = ui.rect.centerx - cancel_w // 2
        cancel_y = ui.rect.bottom - 30

        ui.cancel_button_rect = py.Rect(cancel_x, cancel_y, cancel_w, cancel_h)
        py.draw.rect(screen, color, ui.cancel_button_rect, border_radius=8)

        text = self.font.render("Cancel", True, "#FFFFFF")
        screen.blit(text, text.get_rect(center=ui.cancel_button_rect.center))

    def _update_hover(self, screen):
        ui = self.ui
        mx, my = py.mouse.get_pos()
        hovered = None

        for rect, recipe in ui.recipe_rects:
            if rect.collidepoint(mx, my):
                hovered = recipe
                break

        if hovered != self._hovered_recipe:
            self._hovered_recipe = hovered
            self._hover_panel_visible = bool(hovered)

        if self._hover_panel_visible:
            self.recipe_ui.draw_recipe_panel(screen, self._hovered_recipe, ui.rect, ui.panel_side)
