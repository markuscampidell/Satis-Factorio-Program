# ui.producing_machine_renderer
import pygame as py

from constants.itemdata import get_item_by_id
from ui.recipe_ui import RecipeUI


class ProducingMachineRenderer:
    """Draws a ProducingMachineUI's panel: slots, recipes, progress bar,
    processing arrow. Reads/writes the UI's rect and hit-test rect lists."""
    SLOT_SIZE = 48
    PADDING = 10

    def __init__(self, machine_ui):
        self.machine_ui = machine_ui
        self.font = py.font.SysFont("Arial", 24)
        self.font_small = py.font.SysFont("Arial", 16)
        self.font_tiny = py.font.SysFont("Arial", 10)
        self.recipe_ui = RecipeUI()
        self._hovered_recipe = None
        self._hover_panel_visible = False

    def draw(self, screen):
        ui = self.machine_ui
        if not ui.open or not ui.selected_machine:
            return
        screen.blit(ui.sprite, ui.rect)
        self._draw_progress_bar(screen)
        self._draw_slots(screen)
        self._draw_recipes(screen)

        self._update_recipe_panel(screen)

    def _update_recipe_panel(self, screen):
        ui = self.machine_ui
        mx, my = py.mouse.get_pos()
        hovered_recipe = None
        if ui.recipe_rects and mx is not None and my is not None:
            for rect, recipe in ui.recipe_rects:
                if rect.collidepoint(mx, my):
                    hovered_recipe = recipe
                    break

        self._hovered_recipe = hovered_recipe
        self._hover_panel_visible = bool(hovered_recipe)

        if self._hover_panel_visible and self._hovered_recipe:
            self.recipe_ui.draw_recipe_panel(screen, self._hovered_recipe, ui.rect, ui.panel_side)

    def _draw_progress_bar(self, screen):
        """Draws the processing progress bar."""
        ui = self.machine_ui
        machine = ui.selected_machine
        bar_width, bar_height = 300, 20
        bar_x = ui.rect.centerx - bar_width // 2
        bar_y = ui.rect.bottom - bar_height - 15
        bg_rect = py.Rect(bar_x, bar_y, bar_width, bar_height)
        py.draw.rect(screen, "#9A98B5", bg_rect, border_radius=6)
        progress = min(getattr(machine, "process_timer", 0) / getattr(machine, "process_time", 1), 1.0) if getattr(machine, "processing", False) and getattr(machine, "process_time", 0) > 0 else 0.0
        fill_rect = py.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        py.draw.rect(screen, (0, 230, 0), fill_rect, border_radius=6)
        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        screen.blit(percent_text, percent_text.get_rect(center=bg_rect.center))

    def _draw_recipes(self, screen):
        """Draws the list of recipes, highlighting the selected one and showing output sprites."""
        ui = self.machine_ui
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

    def _draw_slots(self, screen):
        """Draws input and output slots and the processing arrow."""
        ui = self.machine_ui
        ui.slot_rects.clear()
        padding = 40
        input_y = ui.rect.y + padding
        output_y = ui.rect.bottom - padding - self.SLOT_SIZE
        input_x = output_x = ui.rect.x + padding
        self._draw_input_slots(screen, input_x, input_y, ui.selected_machine.recipe.inputs_per_minute())
        self._draw_output_slots(screen, output_x, output_y, ui.selected_machine.output_inventories, ui.selected_machine.recipe.outputs_per_minute())
        self._draw_processing_arrow(screen)

    def _draw_input_slots(self, screen, x, y, inputs_per_min):
        """Draws input slots with item sprites and rates."""
        ui = self.machine_ui
        slot_spacing = 10
        for i, item_id in enumerate(inputs_per_min.keys()):
            rect = py.Rect(x + i * (self.SLOT_SIZE + slot_spacing), y, self.SLOT_SIZE, self.SLOT_SIZE)
            # Draw slot border only (no filled background)
            py.draw.rect(screen, "#AAAAAA", rect, 2)
            slot = ui.selected_machine.input_inventories[item_id].slots[0][0] if ui.selected_machine.input_inventories[item_id].slots[0] else None
            if slot:
                self._draw_item_in_slot(screen, slot, rect)
            text = self.font_small.render(f"{inputs_per_min[item_id]:.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))
            ui.slot_rects.append(rect)

    def _draw_output_slots(self, screen, x, y, output_inventories, outputs_per_min):
        """Draws output slots with item sprites and rates."""
        ui = self.machine_ui
        slot_spacing = 10
        for i, (item_id, inv) in enumerate(output_inventories.items()):
            rect = py.Rect(x + i * (self.SLOT_SIZE + slot_spacing), y, self.SLOT_SIZE, self.SLOT_SIZE)
            # Draw slot border only (no filled background)
            py.draw.rect(screen, "#AAAAAA", rect, 2)
            slot = inv.slots[0][0] if inv.slots[0] else None
            if slot:
                self._draw_item_in_slot(screen, slot, rect)
            text = self.font_small.render(f"{outputs_per_min.get(item_id, 0):.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))
            ui.slot_rects.append(rect)

    def _draw_processing_arrow(self, screen):
        """Draws the animated processing arrow between input and output slots."""
        ui = self.machine_ui
        m = ui.selected_machine
        arrow_w, arrow_h = 20, 40
        padding = 55
        x = ui.rect.x + padding
        y = ui.rect.y + ui.rect.height // 2 - arrow_h // 2
        active = m.processing or (m.recipe and all(m.input_inventories[i].get_amount(i) >= amt for i, amt in m.recipe.inputs.items()))
        base_color = (50, 50, 50)
        target_color = (0, 230, 0)
        fade_speed = 0.1
        if not hasattr(self, "_arrow_color"):
            self._arrow_color = target_color if active else base_color
        current = list(self._arrow_color)
        desired = target_color if active else base_color
        for i in range(3):
            current[i] += (desired[i] - current[i]) * fade_speed
        self._arrow_color = tuple(int(c) for c in current)
        points = [
            (x, y),
            (x + arrow_w, y),
            (x + arrow_w, y + arrow_h - arrow_w // 2),
            (x + arrow_w * 1.5, y + arrow_h - arrow_w // 2),
            (x + arrow_w // 2, y + arrow_h),
            (x - arrow_w // 2, y + arrow_h - arrow_w // 2),
            (x, y + arrow_h - arrow_w // 2)
        ]
        py.draw.polygon(screen, self._arrow_color, points)

    def _draw_item_in_slot(self, screen, slot, rect):
        """Draws an item sprite and amount in a slot rectangle."""
        py.draw.rect(screen, "#AAAAAA", rect, 2)
        item = get_item_by_id(slot["item"]) if isinstance(slot["item"], str) else slot["item"]
        if item and hasattr(item, "sprite") and item.sprite:
            slot_size = self.SLOT_SIZE - 10
            img = item.get_scaled_sprite(slot_size) if hasattr(item, 'get_scaled_sprite') else py.transform.scale(item.sprite, (slot_size, slot_size))
            if img:
                screen.blit(img, (rect.x + 5, rect.y + 5))
        amount = slot["amount"]
        text = self.font_tiny.render(str(amount), True, "#000000")
        text_rect = text.get_rect(bottomright=(rect.right - 5, rect.bottom - 5))
        screen.blit(text, text_rect)
