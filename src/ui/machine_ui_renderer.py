# ui.machine_ui_renderer
import pygame as py

from ui.machine_slot_renderer import MachineSlotRenderer
from ui.machine_recipe_list_renderer import MachineRecipeListRenderer


class MachineUIRenderer:
    """Draws a ProducingMachineUI's panel: background, progress bar, slots,
    and recipe list. Reads/writes the UI's rect and hit-test rect lists.

    Not to be confused with drawing a machine's in-world sprite on the map -
    that's Machine.draw(), called from WorldRenderer. This only draws the
    popup panel shown while a machine is selected."""

    def __init__(self, machine_ui):
        self.machine_ui = machine_ui
        self.font = py.font.SysFont("Arial", 24)
        self.slot_renderer = MachineSlotRenderer()
        self.recipe_list_renderer = MachineRecipeListRenderer()

    def draw(self, screen):
        ui = self.machine_ui
        if not ui.open or not ui.selected_machine:
            return

        screen.blit(ui.sprite, ui.rect)
        self._draw_progress_bar(screen)
        self.slot_renderer.draw(screen, ui)
        self.recipe_list_renderer.draw(screen, ui)

    def _draw_progress_bar(self, screen):
        ui = self.machine_ui
        machine = ui.selected_machine
        bar_width, bar_height = 300, 20
        bar_x = ui.rect.centerx - bar_width // 2
        bar_y = ui.rect.bottom - bar_height - 15

        bg_rect = py.Rect(bar_x, bar_y, bar_width, bar_height)
        py.draw.rect(screen, "#9A98B5", bg_rect, border_radius=6)

        processing = getattr(machine, "processing", False)
        process_time = getattr(machine, "process_time", 0)
        progress = (
            min(getattr(machine, "process_timer", 0) / process_time, 1.0)
            if processing and process_time > 0
            else 0.0
        )

        fill_rect = py.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        py.draw.rect(screen, (0, 230, 0), fill_rect, border_radius=6)

        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        screen.blit(percent_text, percent_text.get_rect(center=bg_rect.center))
