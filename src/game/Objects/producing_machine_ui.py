import pygame as py
from constants.itemdata import get_item_by_id
from game.Objects.machines.producing_machine import ProducingMachine

class ProducingMachineUI:
    def __init__(self, screen_width, screen_height):
        self.image = py.Surface((800, 300))
        self.image.fill("#CAC8E4")
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width//2, screen_height//2)
        self.font = py.font.SysFont("Arial", 24)

        self.open = False
        self.selected_machine = None
        self.dragging = False
        self.drag_offset = (0, 0)

        self.recipe_rects = []
        self.slot_size = 48
        self.input_slot_rect = py.Rect(0, 0, self.slot_size, self.slot_size)
        self.output_slot_rect = py.Rect(0, 0, self.slot_size, self.slot_size)
        self.slot_rects = []

        self.image.set_alpha(220)
    
    def handle_event(self, event, machines, camera, screen, just_placed, placing_machine, player, player_inventory_ui, screen_width, screen_height, dev_mode=False):
        if placing_machine or just_placed: return

        is_mouse_event = event.type in (py.MOUSEBUTTONDOWN, py.MOUSEBUTTONUP, py.MOUSEMOTION)
        mx, my = event.pos if is_mouse_event else (None, None)
        left_click = event.type == py.MOUSEBUTTONDOWN and event.button == 1

        self.handle_drag(event, mx, my)
        if self.open and self.selected_machine:
            self.handle_recipe_click(left_click, mx, my, player, dev_mode=dev_mode)
            self.handle_close_click(left_click, mx, my, player_inventory_ui)
            self.handle_visibility(camera, screen, screen_width, screen_height)
        if not self.open and left_click:
            self.handle_open_click(mx, my, machines, camera)

    def handle_drag(self, event, mx, my):
        if mx is None or my is None: return
        mouse_over_slot = any(rect.collidepoint(mx, my) for rect in self.slot_rects)

        if event.type == py.MOUSEBUTTONDOWN and event.button == 1 and not mouse_over_slot:
            if self.rect.collidepoint(mx, my):
                self.dragging = True
                self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        elif event.type == py.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == py.MOUSEMOTION and self.dragging:
            self.rect.x = mx - self.drag_offset[0]
            self.rect.y = my - self.drag_offset[1]
    def handle_recipe_click(self, left_click, mx, my, player, dev_mode=False):
        if left_click:
            for rect, recipe in self.recipe_rects:
                if rect.collidepoint(mx, my): self.selected_machine.set_recipe(recipe, player_inventory=player.inventory, dev_mode=dev_mode) ; return
    def handle_close_click(self, left_click, mx, my, player_inventory_ui):
        if left_click:
            if self.rect.collidepoint(mx, my): return
            if player_inventory_ui.open and player_inventory_ui.rect.collidepoint(mx, my): return
            self.close()
    def handle_visibility(self, camera, screen, screen_width, screen_height):
        if not self.selected_machine: return
        if not screen.get_rect().colliderect(self.selected_machine.rect.move(-camera.x, -camera.y)): 
            self.close()
            self.rect.center = (screen_width//2, screen_height//2)
    def handle_open_click(self, mx, my, machines, camera):
        for machine in machines:
            if not isinstance(machine, ProducingMachine): continue
            machine_screen_rect = machine.rect.move(-camera.x, -camera.y)
            if machine_screen_rect.collidepoint(mx, my):
                self.open = True
                self.selected_machine = machine
                return
 
    def update_slot_positions(self):
        padding = 20
        self.input_slot_rect.topleft = (self.rect.x + padding, self.rect.y + 80)
        self.output_slot_rect.topleft = (self.rect.x + padding, self.rect.y + 160)
    
    
    def draw(self, screen):
        if not self.open or not self.selected_machine: return
        self.update_slot_positions()
        screen.blit(self.image, self.rect)
        self.draw_progress_bar(screen)
        self.draw_slots(screen)
        self.draw_recipes(screen)

    def draw_progress_bar(self, screen):
        if not isinstance(self.selected_machine, ProducingMachine): return
        machine = self.selected_machine
        bar_width, bar_height = 400, 20
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom - bar_height - 15
        bg_rect = py.Rect(bar_x, bar_y, bar_width, bar_height)
        py.draw.rect(screen, "#9A98B5", bg_rect, border_radius=6)

        if machine.processing and machine.process_time > 0:
            progress = machine.process_timer / machine.process_time ; progress = min(progress, 1.0)
        else: progress = 0.0

        fill_rect = py.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        py.draw.rect(screen, (0, 230, 0), fill_rect, border_radius=6)

        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        percent_rect = percent_text.get_rect(center=bg_rect.center)
        screen.blit(percent_text, percent_rect)
    def draw_recipes(self, screen):
        if not isinstance(self.selected_machine, ProducingMachine): return
        padding = 15
        self.recipe_rects.clear()
        right_edge = self.rect.right - padding
        y = self.rect.y + padding

        title = self.font.render("Recipes:", True, "#000000")
        title_rect = title.get_rect(topright=(right_edge, y))
        screen.blit(title, title_rect)
        y += title_rect.height + 15

        for i, recipe in enumerate(self.selected_machine.recipes):
            text = self.font.render(recipe.name, True, "#000000")
            rect = text.get_rect(topright=(right_edge, y))
            screen.blit(text, rect)
            self.recipe_rects.append((rect, recipe))
            y += rect.height + 10  
    def draw_slots(self, screen):
        if not isinstance(self.selected_machine, ProducingMachine): return

        self.slot_rects.clear()
        padding = 40
        slot_spacing = 10
        font = py.font.SysFont("Arial", 16)
        input_y = self.rect.y + padding
        input_x = self.rect.x + padding
        slot_index = 0

        for item_id, inv in self.selected_machine.input_inventories.items():
            for i in range(inv.width):
                x = input_x + slot_index * (self.slot_size + slot_spacing)
                rect = py.Rect(x, input_y, self.slot_size, self.slot_size)
                py.draw.rect(screen, "#8E8CB8", rect, border_radius=6)
                slot = inv.slots[0][i] if i < len(inv.slots[0]) else None
                if slot: self.draw_item_in_slot(screen, slot, rect)
                amt_per_min = self.selected_machine.inputs_per_minute().get(item_id, 0)
                text = font.render(f"{amt_per_min:.0f}/min", True, "#000000")
                screen.blit(text, (rect.centerx - text.get_width()//2, rect.y - 18))
                self.slot_rects.append(rect)
                slot_index += 1

        output_y = self.rect.bottom - padding - self.slot_size
        output_x = self.rect.x + padding
        inv = self.selected_machine.output_inventory

        for i, item_id in enumerate(self.selected_machine.recipe.outputs):
            x = output_x + i * (self.slot_size + slot_spacing)
            rect = py.Rect(x, output_y, self.slot_size, self.slot_size)
            py.draw.rect(screen, "#8E8CB8", rect, border_radius=6)
            slot = inv.slots[0][i] if i < len(inv.slots[0]) else None
            if slot: self.draw_item_in_slot(screen, slot, rect)
            amt_per_min = self.selected_machine.outputs_per_minute().get(item_id, 0)
            text = font.render(f"{amt_per_min:.0f}/min", True, "#000000")
            screen.blit(text, (rect.centerx - text.get_width()//2, rect.y - 18))
            self.slot_rects.append(rect)
        self.draw_processing_arrow(screen)

    def draw_processing_arrow(self, screen):
        if not self.selected_machine: return

        m = self.selected_machine
        arrow_w, arrow_h = 20, 40
        padding = 55
        x = self.rect.x + padding ; y = self.rect.y + self.rect.height // 2 - arrow_h // 2
        base = (50, 50, 50) ; target = (0, 230, 0) ; fade_speed = 0.1

        active = False
        if m.processing: active = True
        elif m.recipe and all(m.input_inventories[i].get_amount(i) >= amt for i, amt in m.recipe.inputs.items()):
            active = True
        desired_color = target if active else base

        if not hasattr(self, "_arrow_color"): self._arrow_color = desired_color
        current = list(self._arrow_color)
        for i in range(3):
            diff = desired_color[i] - current[i] ; current[i] += diff * fade_speed
        self._arrow_color = tuple(int(c) for c in current)

        points = [(x, y), (x + arrow_w, y), (x + arrow_w, y + arrow_h - arrow_w // 2), (x + arrow_w * 1.5, y + arrow_h - arrow_w // 2),
                  (x + arrow_w // 2, y + arrow_h), (x - arrow_w // 2, y + arrow_h - arrow_w // 2), (x, y + arrow_h - arrow_w // 2)]
        py.draw.polygon(screen, self._arrow_color, points)
    def draw_item_in_slot(self, screen, slot, rect):
        raw = slot["item"]
        if isinstance(raw, str): item = get_item_by_id(raw)
        else: item = raw
        amount = slot["amount"]
        if item and hasattr(item, "image") and item.image:
            image = py.transform.scale(item.image, rect.size)
            screen.blit(image, rect.topleft)
        amount_text = self.font.render(str(amount), True, "#000000")
        screen.blit(amount_text, amount_text.get_rect(bottomright=rect.bottomright))

    def close(self):
        self.open = False
        self.selected_machine = None