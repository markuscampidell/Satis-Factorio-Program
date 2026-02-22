import pygame as py

from constants.itemdata import get_item_by_id

class RecipeUI:
    def __init__(self):
        pass

    def draw_recipe_panel(self, screen, recipe, parent_rect, panel_side):
        """Draws a panel explaining the recipe: name, inputs, outputs, production time."""
        panel_width, panel_height = 320, 180

        if panel_side == "right":
            panel_x = parent_rect.right + 10
        elif panel_side == "left":
            panel_x = parent_rect.left - panel_width - 10
        else:
            panel_x = parent_rect.right + 10  # fallback

        panel_y = parent_rect.y + 40
        panel_rect = py.Rect(panel_x, panel_y, panel_width, panel_height)
        panel = py.Surface((panel_width, panel_height), py.SRCALPHA)
        # Consistent color, alpha, and rounded corners
        color = (202, 200, 228, 220)  # #CAC8E4 with alpha 220
        py.draw.rect(panel, color, panel.get_rect(), border_radius=18)
        font = py.font.SysFont("Arial", 20)
        small_font = py.font.SysFont("Arial", 16)

        # Recipe name
        name_surf = font.render(recipe.name, True, "#000000")
        panel.blit(name_surf, (16, 16))

        # Inputs
        panel.blit(small_font.render("Inputs:", True, "#000000"), (16, 48))
        x = 90
        for item_id, amount in recipe.inputs.items():
            item = get_item_by_id(item_id)
            if item and hasattr(item, "sprite") and item.sprite:
                sprite = py.transform.scale(item.sprite, (24, 24))
                panel.blit(sprite, (x, 48))
            panel.blit(small_font.render(f"x{amount}", True, "#000000"), (x + 28, 52))
            x += 70

        # Outputs
        panel.blit(small_font.render("Outputs:", True, "#000000"), (16, 88))
        x = 90
        for item_id, amount in recipe.outputs.items():
            item = get_item_by_id(item_id)
            if item and hasattr(item, "sprite") and item.sprite:
                sprite = py.transform.scale(item.sprite, (24, 24))
                panel.blit(sprite, (x, 88))
            panel.blit(small_font.render(f"x{amount}", True, "#000000"), (x + 28, 92))
            x += 70

        # Production time
        panel.blit(small_font.render(f"Production time: {getattr(recipe, 'process_time', 1.0):.2f}s", True, "#000000"), (16, 130))

        screen.blit(panel, panel_rect)
        