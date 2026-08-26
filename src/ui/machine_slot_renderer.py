# ui.machine_slot_renderer
import pygame as py

from constants.itemdata import get_item_by_id
from ui.slot_drawing import draw_item_slot_contents


class MachineSlotRenderer:
    """Draws a producing machine's input/output slots (item sprite, amount,
    per-minute rate) and the animated processing arrow between them."""

    SLOT_SIZE = 48
    GHOST_ALPHA = 100  # low opacity

    def __init__(self):
        self.font_small = py.font.SysFont("Arial", 16)
        self.font_tiny = py.font.SysFont("Arial", 10)
        self._arrow_color = None
        self._ghost_sprite_cache = {}

    def draw(self, screen, ui):
        ui.slot_rects.clear()
        padding = 40
        input_y = ui.rect.y + padding
        output_y = ui.rect.bottom - padding - self.SLOT_SIZE
        input_x = output_x = ui.rect.x + padding

        machine = ui.selected_machine
        self._draw_input_slots(screen, ui, input_x, input_y, machine.recipe.inputs_per_minute())
        self._draw_output_slots(screen, ui, output_x, output_y, machine.output_inventories, machine.recipe.outputs_per_minute())
        self._draw_processing_arrow(screen, ui)

    def _draw_input_slots(self, screen, ui, x, y, inputs_per_min):
        slot_spacing = 10
        for i, item_id in enumerate(inputs_per_min.keys()):
            rect = py.Rect(x + i * (self.SLOT_SIZE + slot_spacing), y, self.SLOT_SIZE, self.SLOT_SIZE)
            py.draw.rect(screen, "#AAAAAA", rect, 2)
            slot = ui.selected_machine.input_inventories[item_id].slots[0][0] if ui.selected_machine.input_inventories[item_id].slots[0] else None
            if slot:
                draw_item_slot_contents(screen, slot, rect, self.font_tiny)
            else:
                self._draw_ghost_item(screen, item_id, rect)
            text = self.font_small.render(f"{inputs_per_min[item_id]:.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))
            ui.slot_rects.append((rect, item_id, "input"))

    def _draw_output_slots(self, screen, ui, x, y, output_inventories, outputs_per_min):
        slot_spacing = 10
        for i, (item_id, inv) in enumerate(output_inventories.items()):
            rect = py.Rect(x + i * (self.SLOT_SIZE + slot_spacing), y, self.SLOT_SIZE, self.SLOT_SIZE)
            py.draw.rect(screen, "#AAAAAA", rect, 2)
            slot = inv.slots[0][0] if inv.slots[0] else None
            if slot:
                draw_item_slot_contents(screen, slot, rect, self.font_tiny)
            else:
                self._draw_ghost_item(screen, item_id, rect)
            text = self.font_small.render(f"{outputs_per_min.get(item_id, 0):.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))
            ui.slot_rects.append((rect, item_id, "output"))

    def _draw_processing_arrow(self, screen, ui):
        m = ui.selected_machine
        arrow_w, arrow_h = 20, 40
        padding = 55
        x = ui.rect.x + padding
        y = ui.rect.y + ui.rect.height // 2 - arrow_h // 2

        active = m.processing or (m.recipe and all(m.input_inventories[i].get_amount(i) >= amt for i, amt in m.recipe.inputs.items()))
        base_color = (50, 50, 50)
        target_color = (0, 230, 0)
        fade_speed = 0.1

        if self._arrow_color is None:
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

    def _draw_ghost_item(self, screen, item_id, rect):
        """Faint preview of the item type this empty slot expects."""
        ghost = self._get_ghost_sprite(item_id)
        if ghost:
            screen.blit(ghost, (rect.x + 5, rect.y + 5))

    def _get_ghost_sprite(self, item_id):
        if item_id in self._ghost_sprite_cache:
            return self._ghost_sprite_cache[item_id]

        item = get_item_by_id(item_id)
        ghost = None
        if item and hasattr(item, "sprite") and item.sprite:
            slot_size = self.SLOT_SIZE - 10
            base = item.get_scaled_sprite(slot_size) if hasattr(item, 'get_scaled_sprite') else py.transform.scale(item.sprite, (slot_size, slot_size))
            if base:
                # Copy before fading - get_scaled_sprite returns a cached
                # surface shared with every other place that draws this
                # item, so set_alpha on it directly would fade those too.
                ghost = base.copy()
                ghost.set_alpha(self.GHOST_ALPHA)

        self._ghost_sprite_cache[item_id] = ghost
        return ghost
