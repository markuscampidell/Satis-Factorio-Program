import pygame as py
from constants.itemdata import get_item_by_id
from objects.machines.producing_machine import ProducingMachine

class ProducingMachineUI:
    def __init__(self, screen_width, screen_height, world, camera, player, player_inventory_ui, screen):
        self.sprite = py.Surface((800, 300))
        self.sprite.fill("#CAC8E4")
        self.rect = self.sprite.get_rect(center=(screen_width // 2, screen_height // 2))
        self.font = py.font.SysFont("Arial", 24)

        self.open = False
        self.selected_machine = None
        self.dragging = False
        self.drag_offset = (0, 0)

        self.slot_size = 48
        self.slot_rects = []
        self.recipe_rects = []

        self.sprite.set_alpha(220)

        # References to game objects for interactions
        self.world = world
        self.camera = camera
        self.player = player
        self.player_inventory_ui = player_inventory_ui
        self.screen = screen



    def handle_event(self, event, just_placed, placing_machine):
        if placing_machine or just_placed: return
        mx, my = getattr(event, "pos", (None, None))
        left_click = event.type == py.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1

        self._handle_drag(event, mx, my)

        if self.open and self.selected_machine:
            self._handle_recipe_click(left_click, mx, my)
            self._handle_close_click(left_click, mx, my)
            self._handle_visibility()

    def _handle_drag(self, event, mx, my):
        if mx is None or my is None: return
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mx, my) and not any(r.collidepoint(mx, my) for r in self.slot_rects):
                self.dragging = True
                self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        elif event.type == py.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == py.MOUSEMOTION and self.dragging:
            self.rect.topleft = (mx - self.drag_offset[0], my - self.drag_offset[1])

    def _handle_recipe_click(self, left_click, mx, my):
        if not left_click: return
        for rect, recipe in self.recipe_rects:
            if rect.collidepoint(mx, my):
                self.selected_machine.set_recipe(recipe, player_inventory=self.player.inventory)
                break

    def _handle_close_click(self, left_click, mx, my):
        if not left_click: return
        if self.rect.collidepoint(mx, my): return
        if self.player_inventory_ui.open and self.player_inventory_ui.rect.collidepoint(mx, my): return
        self.close()

    def _handle_visibility(self):
        if not self.selected_machine: return
        if not self.screen.get_rect().colliderect(self.selected_machine.rect.move(-self.camera.x, -self.camera.y)):
            self.close()
            self.rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)

    def draw(self, screen):
        if not self.open or not self.selected_machine: return
        screen.blit(self.sprite, self.rect)
        self._draw_progress_bar(screen)
        self._draw_slots(screen)
        self._draw_recipes(screen)

    def _draw_progress_bar(self, screen):
        machine = self.selected_machine
        bar_width, bar_height = 400, 20
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom - bar_height - 15
        bg_rect = py.Rect(bar_x, bar_y, bar_width, bar_height)
        py.draw.rect(screen, "#9A98B5", bg_rect, border_radius=6)

        progress = 0.0
        if machine.processing and machine.process_time > 0:
            progress = min(machine.process_timer / machine.process_time, 1.0)

        fill_rect = py.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        py.draw.rect(screen, (0, 230, 0), fill_rect, border_radius=6)

        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        screen.blit(percent_text, percent_text.get_rect(center=bg_rect.center))

    def _draw_recipes(self, screen):
        self.recipe_rects.clear()
        padding = 15
        y = self.rect.y + padding
        right_edge = self.rect.right - padding

        title = self.font.render("Recipes:", True, "#000000")
        title_rect = title.get_rect(topright=(right_edge, y))
        screen.blit(title, title_rect)
        y += title_rect.height + 15

        for recipe in getattr(self.selected_machine, "recipes", []):
            text = self.font.render(recipe.name, True, "#000000")
            rect = text.get_rect(topright=(right_edge, y))
            screen.blit(text, rect)
            self.recipe_rects.append((rect, recipe))
            y += rect.height + 10

    def _draw_slots(self, screen):
        self.slot_rects.clear()
        padding = 40
        input_y = self.rect.y + padding
        output_y = self.rect.bottom - padding - self.slot_size
        input_x = output_x = self.rect.x + padding

        self._draw_input_slots(screen, input_x, input_y, self.selected_machine.inputs_per_minute())
        self._draw_output_slots(screen, output_x, output_y, self.selected_machine.output_inventories, self.selected_machine.outputs_per_minute())

        self._draw_processing_arrow(screen)

    def _draw_input_slots(self, screen, x, y, inputs_per_min):
        font = py.font.SysFont("Arial", 16)
        slot_spacing = 10

        for i, item_id in enumerate(inputs_per_min.keys()):
            rect = py.Rect(x + i * (self.slot_size + slot_spacing), y, self.slot_size, self.slot_size)
            py.draw.rect(screen, "#8E8CB8", rect, border_radius=6)

            slot = self.selected_machine.input_inventories[item_id].slots[0][0] if self.selected_machine.input_inventories[item_id].slots[0] else None
            if slot: self._draw_item_in_slot(screen, slot, rect)

            text = font.render(f"{inputs_per_min[item_id]:.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))

            self.slot_rects.append(rect)

    def _draw_output_slots(self, screen, x, y, output_inventories, outputs_per_min):
        font = py.font.SysFont("Arial", 16)
        slot_spacing = 10

        for i, (item_id, inv) in enumerate(output_inventories.items()):
            rect = py.Rect(x + i * (self.slot_size + slot_spacing), y, self.slot_size, self.slot_size)
            py.draw.rect(screen, "#8E8CB8", rect, border_radius=6)

            slot = inv.slots[0][0] if inv.slots[0] else None
            if slot: self._draw_item_in_slot(screen, slot, rect)

            text = font.render(f"{outputs_per_min.get(item_id, 0):.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y - 18))

            self.slot_rects.append(rect)

    def _draw_processing_arrow(self, screen):
        m = self.selected_machine
        arrow_w, arrow_h = 20, 40
        padding = 55
        x = self.rect.x + padding
        y = self.rect.y + self.rect.height // 2 - arrow_h // 2

        active = m.processing or (m.recipe and all(m.input_inventories[i].get_amount(i) >= amt for i, amt in m.recipe.inputs.items()))
        base_color = (50, 50, 50)
        target_color = (0, 230, 0)
        fade_speed = 0.1

        if not hasattr(self, "_arrow_color"): self._arrow_color = target_color if active else base_color
        current = list(self._arrow_color)
        desired = target_color if active else base_color
        for i in range(3): current[i] += (desired[i] - current[i]) * fade_speed
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
        item = get_item_by_id(slot["item"]) if isinstance(slot["item"], str) else slot["item"]
        if item and hasattr(item, "sprite") and item.sprite:
            screen.blit(py.transform.scale(item.sprite, rect.size), rect.topleft)
        amount_text = self.font.render(str(slot["amount"]), True, "#000000")
        screen.blit(amount_text, amount_text.get_rect(bottomright=rect.bottomright))

    def close(self):
        self.open = False
        self.selected_machine = None
    
    def open_for(self, machine):
        self.open = True
        self.selected_machine = machine