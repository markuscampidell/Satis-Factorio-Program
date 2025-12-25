import pygame as py

class PlayerInventoryUI:
    def __init__(self, player):
        self.player = player
        self.open = False
        self.image = py.Surface((600, 400))
        self.image.fill("#CAC8E4")
        self.rect = self.image.get_rect(center=(960, 540))  # center screen
        self.font = py.font.SysFont("Arial", 24)

        self.dragging = False
        self.drag_offset = (0, 0)

    def handle_event(self, event):
        # Screen dragging shenanigans
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                self.dragging = True
                self.drag_offset = (mx - self.rect.x, my - self.rect.y)
        if event.type == py.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if event.type == py.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            self.rect.x = mx - self.drag_offset[0]
            self.rect.y = my - self.drag_offset[1]

    def draw(self, screen):
        if not self.open: return
        screen.blit(self.image, self.rect)
        x, y = self.rect.x + 15, self.rect.y + 15
        for item_id, amount in self.player.inventory.items.items():
            text = self.font.render(f"{item_id}: {amount}", True, "#000000")
            screen.blit(text, (x, y))
            y += 25