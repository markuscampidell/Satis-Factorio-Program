import pygame as py

class MachineUI:
    def __init__(self):
        self.image = py.Surface((800, 300))
        self.image.fill("#CAC8E4")
        self.rect = self.image.get_rect()

        self.open = False
        self.selected_machine = None
        self.recipe_rects = []

        # Font for text
        self.font = py.font.SysFont("Arial", 24)

        self.dragging = False
        self.drag_offset = (0, 0)
    
    def handle_event(self, event, machines, camera, screen, just_placed, building, player, player_inventory_ui):
        if building == True: return
        if just_placed: return

        """cheat code"""
        if event.type == py.KEYDOWN and event.key == py.K_i:
            if self.open and self.selected_machine:
                for item in self.selected_machine.recipe.inputs:
                    self.selected_machine.input_inventory.add(item, 999)
        
        mx, my = None, None
        if event.type in (py.MOUSEBUTTONDOWN, py.MOUSEBUTTONUP, py.MOUSEMOTION):
            mx, my = event.pos

        # Screen dragging shenanigans
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mx, my):
                self.dragging = True
                self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        if event.type == py.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if event.type == py.MOUSEMOTION and self.dragging:
            self.rect.x = mx - self.drag_offset[0]
            self.rect.y = my - self.drag_offset[1]

        # Set recipe when clicking on one
        if self.open and self.selected_machine and event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            for rect, recipe in self.recipe_rects:
                if rect.collidepoint(mx, my):
                    self.selected_machine.set_recipe(recipe, player_inventory=player.inventory)
                    return

        # Check click inside machine_ui, player_inventory_ui and outside
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Inside MachineUI: do nothing
            if self.open and self.selected_machine and self.rect.collidepoint(mx, my): return

            # Inside PlayerInventoryUI: do nothing
            if player_inventory_ui.open and player_inventory_ui.rect.collidepoint(mx, my): return

            self.close()

        # Check if you can open the machine_UI
        if not self.open and event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            for machine in machines:
                dx = machine.rect.centerx - player.rect.centerx
                dy = machine.rect.centery - player.rect.centery
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if distance <= 800 and machine.rect.collidepoint(mx + camera.x, my + camera.y):
                    self.open = True
                    self.selected_machine = machine
                    self.rect.center = screen.get_rect().center
                    return

    def close(self):
        self.open = False
        self.selected_machine = None

    def draw_inputs_outputs(self, screen):
        padding = 15

        left_x = self.rect.x + padding
        y = self.rect.y + padding

        text = self.font.render("Inputs:", True, "#000000")
        screen.blit(text, (left_x, y))
        y += 30

        for item_id, amount in self.selected_machine.input_inventory.items.items():
            line = self.font.render(f"{item_id}: {amount}", True, "#000000")
            screen.blit(line, (left_x, y))
            y += 25

        y += 10
        text = self.font.render("Outputs:", True, "#000000")
        screen.blit(text, (left_x, y))
        y += 30

        for item_id, amount in self.selected_machine.output_inventory.items.items():
            line = self.font.render(f"{item_id}: {amount}", True, "#000000")
            screen.blit(line, (left_x, y))
            y += 25
    
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
    
    def draw_progress_bar(self, screen):
        machine = self.selected_machine

        bar_width = 400
        bar_height = 20
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.bottom - bar_height - 15

        # Background
        bg_rect = py.Rect(bar_x, bar_y, bar_width, bar_height)
        py.draw.rect(screen, "#9A98B5", bg_rect, border_radius=6)

        # Progress fill
        if machine.processing and machine.process_time > 0:
            progress = machine.process_timer / machine.process_time
            progress = min(progress, 1.0)
        else:
            progress = 0.0

        fill_rect = py.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
        py.draw.rect(screen, "#4CAF50", fill_rect, border_radius=6)

        # Percentage text
        percent_text = self.font.render(f"{int(progress * 100)}%", True, "#000000")
        percent_rect = percent_text.get_rect(center=bg_rect.center)
        screen.blit(percent_text, percent_rect)

    def draw(self, screen):
        if not self.open: return
        if not self.selected_machine: return

        # Draw a 800*300 rect
        screen.blit(self.image, self.rect)

        self.draw_inputs_outputs(screen)
        self.draw_recipes(screen)
        self.draw_progress_bar(screen)

        

        