import pygame as py
from constants.itemdata import get_item_by_id

class MachineUI:
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

        self.image.set_alpha(150)
    
    def handle_event(self, event, machines, camera, screen, just_placed, placing_machine, player, player_inventory_ui, screen_width, screen_height):
        if placing_machine or just_placed: return

        is_mouse_event = event.type in (py.MOUSEBUTTONDOWN, py.MOUSEBUTTONUP, py.MOUSEMOTION)
        mx, my = event.pos if is_mouse_event else (None, None)
        left_click = event.type == py.MOUSEBUTTONDOWN and event.button == 1

        self.handle_drag(event, mx, my)
        if self.open and self.selected_machine:
            self.handle_recipe_click(left_click, mx, my, player)
            self.handle_close_click(left_click, mx, my, player_inventory_ui)
            self.handle_visibility(camera, screen, screen_width, screen_height)
        if not self.open and left_click:
            self.handle_open_click(mx, my, machines, camera)

    # Over here should be fine

    def draw_slots(self, screen):
        start_x = self.rect.x + 20
        start_y = self.rect.y + 80

        # ---- INPUT ----
        input_label = self.font.render("Input", True, "#000000")
        screen.blit(input_label, (start_x, start_y - 25))

        input_rect = py.Rect(start_x, start_y, self.slot_size, self.slot_size)
        py.draw.rect(screen, "#8E8CB8", input_rect, border_radius=6)

        slot = self.selected_machine.input_inventory.slots[0][0]
        if slot:
            self.draw_item_in_slot(screen, slot, input_rect)

        # ---- OUTPUT ----
        output_y = start_y + self.slot_size + 40
        output_label = self.font.render("Output", True, "#000000")
        screen.blit(output_label, (start_x, output_y - 25))

        output_rect = py.Rect(start_x, output_y, self.slot_size, self.slot_size)
        py.draw.rect(screen, "#8E8CB8", output_rect, border_radius=6)

        slot = self.selected_machine.output_inventory.slots[0][0]
        if slot:
            self.draw_item_in_slot(screen, slot, output_rect)




    def draw_item_in_slot(self, screen, slot, rect):
        item = get_item_by_id(slot["item"])
        if not item:
            return

        amount = slot["amount"]
        image = py.transform.scale(item.image, rect.size)
        screen.blit(image, rect.topleft)

        amount_text = self.font.render(str(amount), True, "#000000")
        screen.blit(amount_text, amount_text.get_rect(bottomright=rect.bottomright))

    def draw_recipes(self, screen):
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

    # Under here is fine

    def draw_progress_bar(self, screen):
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
        py.draw.rect(screen, "#4CAF50", fill_rect, border_radius=6)

        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        percent_rect = percent_text.get_rect(center=bg_rect.center)
        screen.blit(percent_text, percent_rect)

    def handle_drag(self, event, mx, my):
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mx, my) and not self.input_slot_rect.collidepoint(mx, my) and not self.output_slot_rect.collidepoint(mx, my): 
                self.dragging = True ; self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        if event.type == py.MOUSEBUTTONUP and event.button == 1: self.dragging = False
        if event.type == py.MOUSEMOTION and self.dragging:
            self.rect.x = mx - self.drag_offset[0] ; self.rect.y = my - self.drag_offset[1]

    # Over here is fine

    def handle_recipe_click(self, left_click, mx, my, player):
        if left_click:
            for rect, recipe in self.recipe_rects:
                if rect.collidepoint(mx, my): self.selected_machine.set_recipe(recipe, player_inventory=player.inventory) ; return

    # Under here is fine

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
            machine_screen_rect = machine.rect.move(-camera.x, -camera.y)
            if machine_screen_rect.collidepoint(mx, my):
                self.open = True
                self.selected_machine = machine
                return
    
    # Over here is fine

    def update_slot_positions(self):
        padding = 20
        self.input_slot_rect.topleft = (self.rect.x + padding, self.rect.y + 80)
        self.output_slot_rect.topleft = (self.rect.x + padding, self.rect.y + 160)
    
    # Under here is fine
    def close(self):
        self.open = False
        self.selected_machine = None

    def draw(self, screen):
        if not self.open or not self.selected_machine: return
        self.update_slot_positions()
        screen.blit(self.image, self.rect)
        self.draw_slots(screen)
        self.draw_recipes(screen)
        self.draw_progress_bar(screen)
