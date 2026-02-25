import pygame as py

from constants.itemdata import get_item_by_id

class RecipeUI:
    def __init__(self):
        self.font = py.font.SysFont("Arial", 20)
        self.small_font = py.font.SysFont("Arial", 16)

    def draw_recipe_panel(self, screen, recipe, parent_rect=None, panel_side="right", custom_rect=None):
        """
        Draws a panel explaining the recipe.
        If custom_rect is provided, it draws inside that rect.
        Otherwise it draws left/right of parent_rect.
        """

        panel_width, panel_height = 320, 180

        if custom_rect:
            panel_rect = custom_rect
        else:
            if panel_side == "right":
                panel_x = parent_rect.right + 10
            elif panel_side == "left":
                panel_x = parent_rect.left - panel_width - 10
            else:
                panel_x = parent_rect.right + 10

            panel_y = parent_rect.y + 40
            panel_rect = py.Rect(panel_x, panel_y, panel_width, panel_height)
            
        panel = py.Surface((panel_rect.width, panel_rect.height), py.SRCALPHA)
        py.draw.rect(panel, (202, 200, 228, 220), panel.get_rect(), border_radius=18)

        panel.blit(self.font.render(recipe.name, True, "#000000"), (16, 16))

        panel.blit(self.small_font.render("Inputs:", True, "#000000"), (16, 48))
        x = 90
        for item_id, amount in recipe.inputs.items():
            item = get_item_by_id(item_id)
            if item and item.sprite:
                sprite = py.transform.scale(item.sprite, (24, 24))
                panel.blit(sprite, (x, 48))
            panel.blit(self.small_font.render(f"x{amount}", True, "#000000"), (x + 28, 52))
            x += 70

        panel.blit(self.small_font.render("Outputs:", True, "#000000"), (16, 88))
        x = 90
        for item_id, amount in recipe.outputs.items():
            item = get_item_by_id(item_id)
            if item and item.sprite:
                sprite = py.transform.scale(item.sprite, (24, 24))
                panel.blit(sprite, (x, 88))
            panel.blit(self.small_font.render(f"x{amount}", True, "#000000"), (x + 28, 92))
            x += 70

        process_time = getattr(recipe, "process_time", 1.0)
        panel.blit(
            self.small_font.render(
                f"Production time: {process_time:.2f}s",
                True,
                "#000000"
            ),
            (16, 130)
        )

        screen.blit(panel, panel_rect)