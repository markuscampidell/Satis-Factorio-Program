# ui.machine_recipe_list_renderer
import pygame as py

from constants.itemdata import get_item_by_id
from ui.recipe_ui import RecipeUI


class MachineRecipeListRenderer:
    """Draws a producing machine's available-recipe list (highlighting
    whichever one is active) and the hover panel for whichever recipe the
    mouse is currently over."""

    def __init__(self):
        self.font = py.font.SysFont("Arial", 24)
        self.recipe_ui = RecipeUI()
        self._hovered_recipe = None

    def draw(self, screen, ui):
        ui.recipe_rects.clear()
        padding = 15
        y = ui.rect.y + padding
        right_edge = ui.rect.right - padding

        title = self.font.render("Recipes:", True, "#000000")
        title_rect = title.get_rect(topright=(right_edge, y))
        screen.blit(title, title_rect)
        y += title_rect.height + 15

        selected_index = None
        recipes = getattr(ui.selected_machine, "recipes", [])
        if hasattr(ui.selected_machine, "recipe"):
            for idx, recipe in enumerate(recipes):
                if recipe == ui.selected_machine.recipe:
                    selected_index = idx
                    break

        for i, recipe in enumerate(recipes):
            text = self.font.render(recipe.name, True, "#000000")
            rect = text.get_rect(topright=(right_edge, y))
            recipe_rect = py.Rect(rect.x - 34, rect.y, rect.width + 34, rect.height)

            if i == selected_index:
                py.draw.rect(screen, (255, 165, 0), recipe_rect, border_radius=5)

            sprite_x = recipe_rect.x + 5
            sprite_drawn = False
            for item_id, amount in recipe.outputs.items():
                item = get_item_by_id(item_id)
                if item and hasattr(item, "sprite") and item.sprite:
                    sprite = py.transform.scale(item.sprite, (24, 24))
                    screen.blit(sprite, (sprite_x, recipe_rect.y + (recipe_rect.height - 24) // 2))
                    sprite_drawn = True
                    break

            text_x = sprite_x + (30 if sprite_drawn else 0)
            screen.blit(text, (text_x, rect.y))
            ui.recipe_rects.append((rect, recipe))
            y += rect.height + 10

        self._draw_hover_panel(screen, ui)

    def _draw_hover_panel(self, screen, ui):
        mx, my = py.mouse.get_pos()
        hovered_recipe = None
        for rect, recipe in ui.recipe_rects:
            if rect.collidepoint(mx, my):
                hovered_recipe = recipe
                break

        self._hovered_recipe = hovered_recipe
        if self._hovered_recipe:
            self.recipe_ui.draw_recipe_panel(screen, self._hovered_recipe, ui.rect, ui.panel_side)
